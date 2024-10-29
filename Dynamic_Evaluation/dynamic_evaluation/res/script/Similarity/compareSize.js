const baseline_data = require("../../hadoop/baseline.json");

const compare_data_path = "../../hadoop/leonid_m.json";

// 存储 empty_case， common_case
const project_name = compare_data_path.split("/").pop().split(".")[0];

const compare_data = require(compare_data_path);

const fs = require("fs");

const compareSizeCountFailed = (baseline_data, compare_data) => {
  let compiled_failed_number = 0;
  const common_case = [];
  const insufficient_case = [];
  const redundant_case = [];
  compare_data.forEach((item) => {
    if (!item.successful) {
      compiled_failed_number++;
    } else {
      const baseline_item = baseline_data.find((b) => b.uuid === item.uuid);
      const baseline_item_size =
        baseline_item.uuidMap.projects[0].unitTest[0].predictionSize;
      const item_size = item.uuidMap.projects[0].unitTest[0].predictionSize;
      if (baseline_item_size === 0 && item_size !== 0) {
        redundant_case.push({
          uuid: item.uuid,
          baseline_size: baseline_item_size,
          compare_size: item_size,
        });
      } else if (baseline_item_size !== 0 && item_size === 0) {
        insufficient_case.push({
          uuid: item.uuid,
          baseline_size: baseline_item_size,
          compare_size: item_size,
        });
      } else {
        common_case.push({
          uuid: item.uuid,
          baseline_size:
            baseline_item.uuidMap.projects[0].unitTest[0].predictionSize,
          compare_size: item.uuidMap.projects[0].unitTest[0].predictionSize,
        });
      }
    }
  });

  console.log(
    `compiled_failed_number: ${compiled_failed_number}, redundant_case: ${redundant_case.length}, insufficient_case: ${insufficient_case.length} common_case: ${common_case.length}`
  );

  fs.writeFileSync(
    `../data/${project_name}/insufficient.json`,
    JSON.stringify(insufficient_case, null, 2),
    "utf8"
  );
  fs.writeFileSync(
    `../data/${project_name}/redundant.json`,
    JSON.stringify(redundant_case, null, 2),
    "utf8"
  );
  fs.writeFileSync(
    `../data/${project_name}/common.json`,
    JSON.stringify(common_case, null, 2),
    "utf8"
  );
};

// 分析 common.json
const analyzeSize = (data) => {
  // size 差距在 50% 以上的
  const large_diff = data.reduce((arr, item) => {
    const diff = Math.abs(item.baseline_size - item.compare_size);
    if (diff / item.baseline_size > 0.5) {
      arr.push({
        uuid: item.uuid,
        baseline_size: item.baseline_size,
        compare_size: item.compare_size,
        diff: diff,
      });
    }
    return arr;
  }, []);

  // size 比原来大的
  const larger = data.reduce((arr, item) => {
    if (item.compare_size > item.baseline_size) {
      arr.push({
        uuid: item.uuid,
        baseline_size: item.baseline_size,
        compare_size: item.compare_size,
      });
    }
    return arr;
  }, []);

  // size 比原来小的
  const smaller = data.reduce((arr, item) => {
    if (item.compare_size < item.baseline_size) {
      arr.push({
        uuid: item.uuid,
        baseline_size: item.baseline_size,
        compare_size: item.compare_size,
      });
    }
    return arr;
  }, []);

  console.log(
    `large_diff: ${large_diff.length}, larger: ${larger.length}, smaller: ${smaller.length}`
  );
};

const common_case_data = require(`../data/${project_name}/common.json`);

analyzeSize(common_case_data);
