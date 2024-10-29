const fs = require("fs");
const path = require("path");
// 搜索所有的文件夹，找到可能运行的测试类

const projectDirList = [];

// 寻找所有既有 pom.xml 又有 src/test 的目录
function findAvailableTestClass(directory) {
  const files = fs.readdirSync(directory);
  const hasPomXml = files.includes("pom.xml");
  const hasSrcTest =
    files.includes("src") &&
    fs.readdirSync(path.join(directory, "src")).includes("test");

  if (hasPomXml && hasSrcTest) {
    projectDirList.push(directory);
  }

  const subdirectories = files
    .filter((file) => fs.statSync(path.join(directory, file)).isDirectory())
    .map((subdirectory) => path.join(directory, subdirectory));

  subdirectories.forEach((subdirectory) => {
    findAvailableTestClass(subdirectory);
  });
}

findAvailableTestClass("// YOUR PATH //hadoop-3.4.0-src/");

// 检测 projectDirList中 item/src/test 的目录里面有多少 包含 test 字段的 java 文件
const projectInfo = [];

projectDirList.forEach((item) => {
  let num = 0;
  const testDir = path.join(item, "src", "test");
  const searchFiles = (directory) => {
    const files = fs.readdirSync(directory);
    files.forEach((file) => {
      const filePath = path.join(directory, file);
      if (fs.statSync(filePath).isDirectory()) {
        searchFiles(filePath);
      } else if (file.endsWith(".java")) {
        const content = fs.readFileSync(filePath, "utf8");
        if (content.includes("@Test")) {
          num++;
        }
      }
    });
  };
  searchFiles(testDir);

  if (num > 0) {
    projectInfo.push({
      project: item.replace("// YOUR PATH //hadoop-3.4.0-src/", ""),
      testNum: num,
    });
  }
});

// 将 projectInfo 进行分类，如果 (item.project.split("/").pop()).join('/) 相同则归为一类
const groupedProject = projectInfo.reduce((groups, item) => {
  const key = item.project.split("/").slice(0, -1).join("/");
  if (!groups[key]) {
    groups[key] = [];
  }
  groups[key].push({ ...item, project: item.project.split("/").pop() });
  return groups;
}, {});

// 存储 res
fs.writeFileSync(
  path.join(__dirname, "./potentialDir.json"),
  JSON.stringify(groupedProject, null, 2)
);
