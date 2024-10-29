const { exec } = require("child_process");
const { log, error } = require("console");
const fs = require("fs");
const path = require("path");
const util = require("util");
const args = process.argv.slice(2);
const saveDir = args[0];

const execAsync = util.promisify(exec);

const allCoveredFunctions = require("./data/tagged_prediction_data.json");

function getAllJavaFiles(dirPath, arrayOfFiles = []) {
  const files = fs.readdirSync(dirPath);

  files.forEach((file) => {
    if (fs.statSync(path.join(dirPath, file)).isDirectory()) {
      arrayOfFiles = getAllJavaFiles(path.join(dirPath, file), arrayOfFiles);
    } else {
      if (file.endsWith(".java")) {
        arrayOfFiles.push(path.join(dirPath, file));
      }
    }
  });

  return arrayOfFiles;
}

async function findJavaTestFiles(dir, rules) {
  // 重复判断，如果得到的文件太多，根据数量重新筛选
  let dynamic_rules = rules;
  const files = getAllJavaFiles(dir);
  while (true) {
    // 读取文件内容， 如果长度大于 5000 则进行测试, length 根据项目做不同的筛选
    const filteredFiles = files.filter((file) => {
      const content = fs.readFileSync(file, "utf-8");
      return content.length > dynamic_rules && content.includes("@Test");
    });

    if (filteredFiles.length > 66) {
      dynamic_rules += 500;
      continue;
    }

    // 只留最后的名字
    const fileNames = filteredFiles.map((file) =>
      file.split("/").pop().replace(".java", "")
    );
    return { fileNames, dynamic_rules };
  }
}

async function runMavenTest(className, mvnDir) {
  process.chdir(mvnDir);
  await execAsync(`mvn clean test -Dtest=${className}`, {
    maxBuffer: 1024 * 1024 * 100,
  });
}

async function copyFile(sourceDir, targetDir, filename) {
  fs.copyFileSync(
    path.join(sourceDir, filename),
    path.join(targetDir, filename)
  );
}

async function copyDir(sourceDir, targetDir) {
  fs.cpSync(sourceDir, targetDir, { recursive: true });
}

async function runScripts(targetDir, project, top) {
  console.log("Run scripts ===================");
  process.chdir(targetDir);
  await execAsync(`node getAllLogFunction.js ${project} ${top} ${saveDir}`, {
    maxBuffer: 1024 * 1024 * 1000,
  });
}

async function createDir(targetDir, newDirName) {
  const newDir = path.join(targetDir, newDirName);
  if (!fs.existsSync(newDir)) {
    fs.mkdirSync(newDir);
  }
}

function checkComplieErrror(error, errorFunctionList) {
  if (!error.stdout.includes("COMPILATION ERROR :")) {
    return;
  }
  // 如果出现编译错误，则定位到某一行
  const errorHead = "[\u001b[1;31mERROR\u001b[m]";
  // 去掉不含有错误的行
  const lines = error.stdout
    .split("\n")
    .filter((line) => line.includes(errorHead) && line.includes(".java"));
  lines.forEach((line) => {
    const errorFile =
      line.split("[\u001b[1;31mERROR\u001b[m]")[1].trim().split(".java:")[0] +
      ".java".trim();
    const errorLine = parseInt(
      line.split(".java:")[1].split(",")[0].split("[")[1]
    );
    console.log("This is error file: ", errorFile, errorLine);
    const errorFunction = allCoveredFunctions.find(
      (item) =>
        item.function_position ===
          errorFile.replace(
            "// YOUR PATH ///hadoop/",
            "// YOUR PATH //hadoop_test_platform/"
          ) &&
        parseInt(item.new_function_lines.split("-")[0].trim()) <= errorLine &&
        parseInt(item.new_function_lines.split("-")[1].trim()) >= errorLine
    );
    if (errorFunction) {
      errorFunctionList.push(errorFunction);
      errorFunction.complied = false;
      if (!("errorNums" in errorFunction)) {
        errorFunction.errorNums = 1;
      } else {
        errorFunction.errorNums += 1;
      }
      console.log(
        "\x1b[31m%s\x1b[0m",
        "Error Function: ",
        "\x1b[32m%s\x1b[0m" + errorFunction.function_position,
        "\x1b[31m%s\x1b[0m" + errorFunction.function_name,
        "\x1b[32m%s\x1b[0m" + errorFunction.new_function_lines
      );
    }
  });
}

let SPECIAL = false;
let testList;
if (saveDir === "newTest") {
  testList = require("./data/breakPoiint.json");
} else if (saveDir === "secondTest") {
  testList = require("./afterTest/coveredFuntionTestUnits.json");
} else if (saveDir === "predictionTest") {
  testList = require("./afterTest/avaliableTestList.json");
} else if (saveDir.startsWith("tagTest")) {
  testList = require("./afterTest/coveredFunctionTestUnits.json");
} else if (saveDir.startsWith("errorTest")) {
  testList = require("./afterTest/coveredFunctionTestUnitsMAX.json");
} else if (saveDir.startsWith("sameOutputTest")) {
  testList = require("./A_tagHashTest/mapNew.json");
  SPECIAL = true;
} else if (saveDir.startsWith("hashTag")) {
  testList = require("./A_tagHashTest/mapNew.json");
}

const topProject = [];
// 有的因为测试太多，所以 rules 设置的比较大， 但这里先设置为 0
Object.keys(testList).forEach((key) => {
  topProject.push({
    name: key,
    list: testList[key].map((item) => ({
      name: item.project,
      rules: 0,
      classList: item?.classList || [],
    })),
  });
});

async function main() {
  const saveDirBase = `// YOUR PATH ///hadoop/script/data/${saveDir}/`;
  const scriptDir = "// YOUR PATH ///hadoop/script/";

  const classTest = async (
    javaTestFiles,
    mvnTestDir,
    xmlDir,
    saveDir,
    logsDir,
    projectName,
    top,
    ifFirst,
    ifNeed
  ) => {
    console.log("Need find functions", ifNeed);
    const logs = [];
    for (let className of javaTestFiles) {
      // 出错继续运行循环，打印日志, 如果是第二次运行，则直接拷贝 logs 文件夹
      try {
        console.log("Process class ================= ", className);
        await runMavenTest(className, mvnTestDir);
        console.log("mvn test Done ==================", className);
        // copy jacoco.xml file to saveDir
        ifNeed && (await copyFile(xmlDir, saveDir, "jacoco.xml"));
        // 拿到 jacoco.xml file 后跑脚本，拿到覆盖的 log statement 的函数
        ifNeed && (await runScripts(scriptDir, projectName, top));
        // 判断是否存在 coveredLogsFunctions.json 文件
        if (
          ifNeed &&
          !fs.existsSync(path.join(saveDir, "coveredLogsFunctions.json"))
        ) {
          console.log(
            "No coveredLogsFunctions.json file =================",
            className
          );
          logs.push({
            project: projectName,
            className,
            status: "failed",
            error: "No coveredLogsFunctions.json file",
          });
          continue;
        }
        if (ifNeed && !fs.existsSync(logsDir)) {
          console.log("No logs file =================", className);
          logs.push({
            project: projectName,
            className,
            status: "failed",
            error: "No logs file",
          });
          continue;
        }
        // 如果存在 fundiFunction.json 文件 copy logs to saveDir, 新建文件夹带上时间戳
        const newDirName =
          className + new Date().toISOString().replace(/:/g, "-");
        // 先创建项目文件夹，再创建存储 logs 的文件夹
        await createDir(saveDir, newDirName);
        // 拷贝 logs 文件夹到新建文件夹
        await copyDir(logsDir, path.join(saveDir, newDirName));
        // 拷贝结果
        ifNeed &&
          (await copyFile(
            saveDir,
            path.join(saveDir, newDirName),
            "coveredLogsFunctions.json"
          ));
        // 拷贝 jacoco.xml
        ifNeed &&
          (await copyFile(
            saveDir,
            path.join(saveDir, newDirName),
            "jacoco.xml"
          ));
        // 删除 coveredLogsFunctions.json
        ifNeed &&
          (await fs.unlinkSync(
            path.join(saveDir, "coveredLogsFunctions.json")
          ));
        console.log("Process class =============== ", className, ": Done");
        logs.push({
          project: projectName,
          className,
          status: "success",
          mvnCommand: `mvn clean test -Dtest=${className}`,
          mvnTestDir,
        });
      } catch (error) {
        logs.push({
          project: projectName,
          className,
          status: "failed",
          mvnCommand: `mvn clean test -Dtest=${className}`,
          error: error.stdout,
        });
        console.log("ERROR in Test =================", className);
        console.error("ERROR occurred:", error.stdout);
      }
    }
    // 保存日志
    fs.writeFileSync(path.join(saveDir, `logs.json`), JSON.stringify(logs));
  };

  for (let top of topProject) {
    for (let project of top.list) {
      console.log("Process project ================= ", project.name);
      const testFileTargetDir = `// YOUR PATH ///hadoop/${top.name}/${project.name}/src/test/`;
      const mvnClassTestDir = `// YOUR PATH ///hadoop/${top.name}/${project.name}/`;
      const xmlDir = `// YOUR PATH ///hadoop/${top.name}/${project.name}/target/site/jacoco/`;
      const logsDir = `// YOUR PATH ///hadoop/${top.name}/${project.name}/target/surefire-reports/`;
      const saveClassTestDir = `// YOUR PATH ///hadoop/script/data/${saveDir}/${project.name}/`;

      const ifFirst = !project.classList.length;
      const ifNeed = ifFirst || SPECIAL;

      console.log(ifFirst);
      const { fileNames: javaTestFiles, dynamic_rules } =
        ifFirst && (await findJavaTestFiles(testFileTargetDir, project.rules));
      ifFirst &&
        log(
          `${top.name} / ${project.name}, The rules is ${dynamic_rules}`,
          javaTestFiles.length
        );
      await createDir(saveDirBase, project.name);
      console.log(
        "Project ======== ",
        project.name,
        "Test files: ",
        ifFirst ? javaTestFiles.length : project.classList.length
      );

      // 运行 class 粒度的测试
      await classTest(
        ifFirst ? javaTestFiles : project.classList,
        mvnClassTestDir,
        xmlDir,
        saveClassTestDir,
        logsDir,
        project.name,
        top.name,
        ifFirst,
        ifNeed
      );

      console.log("Current working directory:", process.cwd());
    }
  }

  console.log("All Done");
}

main();
