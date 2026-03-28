# Field Mapping (图签栏字段映射)

## Keywords (中英对照/常见缩写)

- project_name: 项目名称, 工程名称, Project, 工程
- drawing_title: 图名, 图纸名称, Drawing Title, Title
- discipline: 专业, Discipline, 建筑/结构/机电/给排水/暖通/电气/消防/照明
- drawing_no: 图号, 图纸编号, Drawing No., No., 图纸号
- version: 版本, 版次, Revision, Rev., 版本号
- date: 日期, Date, 出图日期
- scale: 比例, Scale, 比例尺
- company: 设计单位, 设计院, 公司, Company, Design Institute
- review_no: 审图号, 审图编号
- review_agency: 审图单位, 审图机构
- design_stage: 设计阶段, 方案/初设/施工图/深化
- drawing_stage: 施工图/过程图/投标图/竣工图
- page_size: 图幅, 图面尺寸, A0/A1/A2/A3
- sheet_index: 张号, 页码, Sheet, Sheet No.

## Regex hints

- date: \d{4}[-./年]\d{1,2}[-./月]\d{1,2}
- scale: 1[:：]\d+
- drawing_no: 字母+数字混合（如 A-101, M-02, S1-03）
- revision: Rev\.?\s*\w+ | 版本\s*\w+
