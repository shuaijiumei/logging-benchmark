const { log } = require("console");
const fs = require("fs");
const xml2js = require("xml2js");
const parser = new xml2js.Parser();
const args = process.argv.slice(2);
const project = args[0];
const top = args[1];
const saveDir = args[2];

const hadoopData = require("./data/hadoop-cleaned.json");

const baseDir = `// YOUR PATH ///hadoop/${top}/${project}/src/main/java/`;

// 路径到您的 Jacoco XML 报告
const xmlFile = `./data/${saveDir}/${project}/jacoco.xml`;

fs.readFile(xmlFile, (err, data) => {
  if (err) {
    console.error("Error reading XML file:", err);
    return;
  }

  // 解析 XML 数据
  parser.parseString(data, (err, result) => {
    if (err) {
      console.error("Error parsing XML data:", err);
      return;
    }

    // 递归地搜索每个类中的每一行
    const packages = result.report.package;
    const coveredLogs = [];
    packages.forEach((pkg) => {
      pkg.sourcefile.forEach((sourcefile) => {
        const fileName = pkg.$.name + "/" + sourcefile.$.name;
        const lines = sourcefile.line || [];
        lines.forEach((line) => {
          // 检查被执行的行是否被覆盖
          if (line.$.ci > 0) {
            try {
              const lineNumber = line.$.nr;

              const filePath = baseDir + fileName;

              const data = fs.readFileSync(filePath, "utf8");
              // 从文件中提取行
              const lines = data.split("\n");
              const logLines = [];
              for (let i = 0; i < lines.length; i++) {
                if (
                  i + 1 == lineNumber &&
                  lines[i].trim().toLocaleLowerCase().startsWith("log.")
                ) {
                  logLines.push(lines[i]);
                  break;
                }
              }
              logLines.map((line) => {
                coveredLogs.push({
                  lineNumber: lineNumber,
                  logLine: line.trim(),
                  position: filePath,
                });
              });
            } catch (e) {
              // 无法读取文件
              console.log("Error reading file: ", e);
            }
          }
        });
      });
    });
    const coveredFunctions = [];

    // 查询 hadoop 源码中的所有日志函数， 是否有 被覆盖的日志函数
    coveredLogs.map((item) => {
      hadoopData.map((log) => {
        if (
          parseInt(log["function_lines"].split("-")[0]) <=
            parseInt(item.lineNumber) &&
          parseInt(log["function_lines"].split("-")[1]) >=
            parseInt(item.lineNumber) &&
          item.position.includes(
            log["function_position"].replace(
              "// YOUR PATH //hadoop_test_platform/",
              ""
            )
          )
        ) {
          coveredFunctions.push({
            ...log,
            coveredLog: [item.logLine],
          });
        }
      });
    });

    const coveredFunctionsMap = {};
    coveredFunctions.map((item) => {
      const key = item.function_name + item.function_position;
      if (coveredFunctionsMap[key]) {
        coveredFunctionsMap[key].coveredLog.push(...item.coveredLog);
      } else {
        coveredFunctionsMap[key] = item;
      }
    });
    const coveredFunctionsArray = Object.values(coveredFunctionsMap);

    log("This is the covered log number: ", coveredFunctionsArray.length);
    if (coveredFunctionsArray.length > 0) {
      fs.writeFileSync(
        `./data/${saveDir}/${project}/coveredLogsFunctions.json`,
        JSON.stringify(coveredFunctionsArray, null, 2)
      );
    }
  });
});
