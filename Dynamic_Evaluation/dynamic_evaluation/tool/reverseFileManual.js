// run in the docker container
const fs = require("fs");

const args = process.argv.slice(2);
const saveDir = args[0];

function reverseFunc(tool) {
  // 先判断是否存在对应的 json 文件
  // 找到路径下唯一的 json 文件
  const jsonPath = fs
    .readdirSync(`../data/${tool}/replaceLogs/`)
    .filter((item) => {
      return item.endsWith(".json");
    })
    .pop();

  const list = require(`../data/${tool}/replaceLogs/${jsonPath}`);
  list.forEach((item) => {
    const { filePath, replaceList } = item;
    let content = fs.readFileSync(filePath, "utf8");
    // 直接用字符串匹配回去
    replaceList.forEach((replaceItem) => {
      const { target, replacement } = replaceItem;
      content = content.replace(replacement, target);
    });
    fs.writeFileSync(filePath, content, "utf8");
  });
  console.log("%cReverse Successfully", "color: green; font-weight: bold;");
  // 将 json 文件改名为 .bak，防止再次替换
  fs.renameSync(
    `../data/${tool}/replaceLogs/${jsonPath}`,
    `../data/${tool}/replaceLogs/${jsonPath}.bak`
  );
}

reverseFunc(saveDir);
