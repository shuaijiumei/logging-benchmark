const { exec } = require("child_process");
const fs = require("fs");
const path = require("path");
const util = require("util");
const JSONStream = require("JSONStream");
const args = process.argv.slice(2);
const saveDir = args[0];
const tool = args[1];

const execAsync = util.promisify(exec);

function writeLargeJSONArrayWithJSONStream(filePath, data) {
  const writeStream = fs.createWriteStream(filePath);
  const jsonStream = JSONStream.stringify("[\n", ",\n", "\n]\n");

  jsonStream.pipe(writeStream);
  data.forEach((item) => {
    jsonStream.write(item);
  });
  jsonStream.end();
}

async function runMavenTest(className, mvnDir) {
  const startTime = new Date().getTime();
  process.chdir(mvnDir);
  await execAsync(`sudo mvn test -Ptest-only -Dtest=${className}`, {
    maxBuffer: 1024 * 1024 * 100,
  });

  const endTime = new Date().getTime();
  const time = (endTime - startTime) / 1000;
  console.log("[TEST TIME]: ", time + "s");
  return time;
}

async function runMavenCompile(mvnDir) {
  process.chdir(mvnDir);
  const { stdout, stderr } = await execAsync(
    `sudo mvn clean install -DskipTests`,
    {
      maxBuffer: 1024 * 1024 * 100,
    }
  );


  if (stdout.includes("BUILD FAILURE")) {
    throw new Error("[COMPILE FAIL!]");
  }
}

async function copyDir(sourceDir, targetDir) {
  fs.cpSync(sourceDir, targetDir, { recursive: true });
}

async function createDir(targetDir, newDirName) {
  const newDir = path.join(targetDir, newDirName);
  if (!fs.existsSync(newDir)) {
    fs.mkdirSync(newDir);
  }
}

function getDir(fileName) {
  return fileName.replaceAll("_", "/").replace(".json", "");
}

function replaceFunc(position, function_lines, prediction, uuid) {
  const logs = [];
  const replaceList = [];
  const replaceLocation = position.replace(
    "path in computer",
    "[PATH IN DOCKER]"
  );
  const content = fs.readFileSync(replaceLocation, {
    encoding: "utf-8",
  });
  const start_line = parseInt(function_lines.split("-")[0].trim());
  const end_line = parseInt(function_lines.split("-")[1].trim());
  const lines = content.split("\n");
  const function_content = lines.slice(start_line - 1, end_line).join("\n");

  replaceList.push({
    target: function_content,
    replacement: prediction,
    lines: function_lines,
  });
  let newContent = content;
  replaceList.forEach((item) => {
    newContent = newContent.replace(item.target, item.replacement);
  });
  logs.push({
    filePath: replaceLocation,
    replaceList,
  });
  fs.writeFileSync(
    path.resolve(
      __dirname,
      `[PATH IN DOCKER]/data/${tool}/replaceLogs/${uuid}.json`
    ),
    JSON.stringify(logs),
    {
      encoding: "utf-8",
    }
  );
  fs.writeFileSync(replaceLocation, newContent, {
    encoding: "utf-8",
  });
  console.log("%cReplace Successfully", "color: green; font-weight: bold;");
}

function reverseFunc(uuid) {
  if (
    !fs.existsSync(`[PATH IN DOCKER] /data/${tool}/replaceLogs/${uuid}.json`) &&
    !fs.existsSync(`[PATH IN DOCKER] /data/${tool}/replaceLogs/${uuid}.bak`)
  ) {
    console.log(
      "%cNo such file or directory",
      "color: red; font-weight: bold;"
    );
    process.exit(1);
  }
  if (
    !fs.existsSync(`[PATH IN DOCKER] /data/${tool}/replaceLogs/${uuid}.json`) &&
    fs.existsSync(`[PATH IN DOCKER] /data/${tool}/replaceLogs/${uuid}.bak`)
  ) {
    // 只是还原过了
    console.log("%cAlready Reversed", "color: green; font-weight: bold;");
    return;
  }

  const list = require(`[PATH IN DOCKER] /data/${tool}/replaceLogs/${uuid}.json`);
  list.forEach((item) => {
    const { filePath, replaceList } = item;
    let content = fs.readFileSync(filePath, "utf8");
    replaceList.forEach((replaceItem) => {
      const { target, replacement } = replaceItem;
      content = content.replace(replacement, target);
    });
    fs.writeFileSync(filePath, content, "utf8");
  });
  console.log("%cReverse Successfully", "color: green; font-weight: bold;");
  fs.renameSync(
    path.resolve(
      __dirname,
      `[PATH IN DOCKER]/data/${tool}/replaceLogs/${uuid}.json`
    ),
    path.resolve(
      __dirname,
      `[PATH IN DOCKER]/data/${tool}/replaceLogs/${uuid}.bak`
    )
  );
}

let predictions = require(`[PATH IN DOCKER]/data/${tool}/test/${tool}.json`);

const runTest = async () => {
  const totalNumber = predictions.length;

  console.log("Total number of test: ", totalNumber);
  for (let func of predictions) {
    replaceFunc(
      func.function_position,
      func.function_lines,
      func.prediction,
      func.uuid
    );

    try {
      const mvnClassTestDir = `// YOUR PATH ///hadoop/${getDir(
        func.uuidMap.top
      )}/${func.uuidMap.projects[0].name}/`;
      console.log("Compile project ================= ", mvnClassTestDir);
      await runMavenCompile(mvnClassTestDir);
      console.log("mvn compile Done ==================", func.uuidMap.top);
      func.successful = true;
      for (let project of func.uuidMap.projects) {
        for (let unit of project.unitTest) {
          const className = unit.name;
          const topName = getDir(func.uuidMap.top);
          console.log("Process project ================= ", project.name);
          const mvnClassTestDir = `// YOUR PATH ///hadoop/${topName}/${project.name}/`;
          const logsDir = `// YOUR PATH ///hadoop/${topName}/${project.name}/target/surefire-reports/`;

          console.log(
            "Process class ================= ",
            className,
            mvnClassTestDir,
            func.uuid
          );

          const time = await runMavenTest(className, mvnClassTestDir);
          console.log("mvn test Done ==================", className);

          if (!fs.existsSync(logsDir)) {
            console.log("No logs file =================", className);
            unit.successful = false;
            continue;
          }

          unit.successful = true;

          const result = fs
            .readdirSync(logsDir)
            .filter((item) => item.endsWith("-output.txt"));

          if (result.length === 0) {
            unit.predictOutput = "";
            unit.testTime = time;
            unit.predictionSize = 0;
            continue;
          }

          const super_tag_content = result.reduce((res, file) => {
            const content = fs
              .readFileSync(path.resolve(logsDir, file), {
                encoding: "utf-8",
              })
              .split("\n")
              .filter((line) => line.includes("[SUPER TAG]"));

            return res.concat(content);
          }, []);

          const filePath = `[PATH IN DOCKER]/data/${tool}/output/${project.name}_${className}_${unit.uuid}.txt`;
          fs.writeFileSync(filePath, super_tag_content.join("\n"));

          const stats = fs.statSync(filePath);
          const fileSizeInBytes = stats.size;

          unit.predictOutput = filePath;
          unit.testTime = time;
          unit.predictionSize = fileSizeInBytes;
        }
      }
    } catch (error) {
      console.log(
        "error reason: ",
        error.stdout.split("\n").filter((line) => line.includes("ERROR"))
      );
      const errorLines = error.stdout.split("\n");
      let errorContent = "";
      for (let i = 0; i < errorLines.length; i++) {
        if (errorLines[i].includes("COMPILATION ERROR :")) {
          for (let j = i; j < i + 10; j++) {
            errorContent += errorLines[j] + "\n";
          }
        }
      }
      const errorFilePath = `[PATH IN DOCKER]/data/${tool}/error/${func.uuid}.txt`;
      fs.writeFileSync(errorFilePath, errorContent);

      console.log(
        `[COMPILE FAIL!] ${func.uuidMap.top}:::func.uuid ${func.uuid}`
      );
      func.successful = false;
    }

    reverseFunc(func.uuid);

    writeLargeJSONArrayWithJSONStream(
      `[PATH IN DOCKER]/data/${tool}/result/${tool}.json`,
      predictions
    );
  }
};


runTest();
