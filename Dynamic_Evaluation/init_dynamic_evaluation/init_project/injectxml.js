// 给所有的子项目的pom.xml文件注入Jacoco插件

const list = require("./potentialDir.json");

const fs = require("fs").promises;
const xml2js = require("xml2js");
const parser = new xml2js.Parser();
const builder = new xml2js.Builder();

async function injectJacocoPlugin(pomPath) {
  try {
    const data = await fs.readFile(pomPath);
    const result = await parser.parseStringPromise(data);

    const jacocoPlugin = {
      groupId: ["org.jacoco"],
      artifactId: ["jacoco-maven-plugin"],
      version: ["0.8.7"],
      configuration: [
        {
          destFile: ["target/jacoco.exec"],
          dataFile: ["target/jacoco.exec"],
        },
      ],
      executions: [
        {
          execution: [
            {
              id: ["jacoco-initialize"],
              goals: [{ goal: ["prepare-agent"] }],
            },
            {
              id: ["check"],
              goals: [{ goal: ["check"] }],
            },
            {
              id: ["jacoco-site"],
              phase: ["test"],
              goals: [{ goal: ["report"] }],
            },
          ],
        },
      ],
    };

    if (!result.project.build) {
      result.project.build = [{}];
    }
    if (!result.project.build[0].plugins) {
      result.project.build[0].plugins = [{}];
    }
    if (!result.project.build[0].plugins[0].plugin) {
      result.project.build[0].plugins[0].plugin = [];
    }
    result.project.build[0].plugins[0].plugin.push(jacocoPlugin);

    const xml = builder.buildObject(result);
    await fs.writeFile(pomPath, xml);
    console.log("pom.xml has been updated with the Jacoco plugin!");
  } catch (err) {
    console.error("Failed to inject Jacoco plugin into pom.xml:", err);
  }
}

async function deleteJacocoPlugin(pomPath) {
  try {
    const data = await fs.readFile(pomPath);
    const result = await parser.parseStringPromise(data);

    if (
      result.project.build &&
      result.project.build[0].plugins &&
      result.project.build[0].plugins[0].plugin
    ) {
      const plugins = result.project.build[0].plugins[0].plugin;
      const jacocoIndex = plugins.findIndex(
        (plugin) => plugin.artifactId[0] === "jacoco-maven-plugin"
      );
      if (jacocoIndex !== -1) {
        plugins.splice(jacocoIndex, 1);
        const xml = builder.buildObject(result);
        await fs.writeFile(pomPath, xml);
        console.log("Jacoco plugin has been removed from pom.xml!");
      } else {
        console.log("Jacoco plugin is not found in pom.xml.");
      }
    } else {
      console.log("No plugins found in pom.xml.");
    }
  } catch (err) {
    console.error("Failed to delete Jacoco plugin from pom.xml:", err);
  }
}

Object.keys(list).forEach((key) => {
  list[key].forEach(async (item) => {
    const pomPath = `// YOUR PATH ///hadoop/${key}/${item.project}/pom.xml`;
    await deleteJacocoPlugin(pomPath);
  });
});
