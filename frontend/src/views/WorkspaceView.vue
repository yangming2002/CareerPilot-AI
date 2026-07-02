<script setup lang="ts">
import { computed, ref } from 'vue'

const mode = ref<'jd' | 'direction'>('jd')
const resumeText = ref('')
const jdText = ref('')
const targetDirection = ref('Agent 开发工程师')
const experienceLevel = ref('校招 / 实习')
const hasReport = ref(false)

const directionOptions = [
  'Agent 开发工程师',
  '算法工程师',
  'Python 后端工程师',
  '测试开发工程师',
  '产品经理',
  '运营岗位',
  '数据分析师',
]

const reportTitle = computed(() => {
  return mode.value === 'jd' ? '指定 JD 匹配报告' : '岗位方向泛化匹配报告'
})

const reportDescription = computed(() => {
  if (mode.value === 'jd') {
    return '系统将基于用户提供的具体 JD 与简历内容，输出匹配度、缺口分析和真实性约束下的优化建议。'
  }

  return '系统将从 JD 知识库抽取同类岗位画像，并结合简历给出通用匹配度、能力短板和岗位推荐。'
})

function runAnalysis() {
  hasReport.value = true
}
</script>

<template>
  <main class="workspace-page">
    <section class="page-header">
      <div>
        <p class="eyebrow">CareerPilot-AI</p>
        <h1>基于 JD 与简历匹配的智能求职优化系统</h1>
        <p class="subtitle">
          JD 可进入知识库，简历默认仅用于本次分析，不持久化存储。
        </p>
      </div>
      <el-tag type="success" effect="light">MVP 前端工作台</el-tag>
    </section>

    <section class="privacy-banner">
      <strong>隐私原则：</strong>
      简历内容默认不入库；JD 数据可沉淀为岗位知识库，用于岗位画像、相似 JD 检索和推荐。
    </section>

    <section class="mode-card">
      <div class="section-title">
        <h2>选择分析模式</h2>
        <span>支持精准 JD 匹配，也支持只有目标方向时的泛化匹配。</span>
      </div>

      <el-radio-group v-model="mode">
        <el-radio-button label="jd">我有具体 JD</el-radio-button>
        <el-radio-button label="direction">我只有目标方向</el-radio-button>
      </el-radio-group>
    </section>

    <section class="input-grid">
      <el-card shadow="never" class="panel-card">
        <template #header>
          <div class="card-header">
            <span>简历内容</span>
            <el-tag size="small" type="warning">不保存</el-tag>
          </div>
        </template>

        <el-input
          v-model="resumeText"
          type="textarea"
          :rows="14"
          resize="none"
          placeholder="请粘贴简历文本。MVP 阶段先支持文本输入，后续再支持 PDF / DOCX 解析。"
        />
      </el-card>

      <el-card shadow="never" class="panel-card">
        <template #header>
          <div class="card-header">
            <span>{{ mode === 'jd' ? '岗位 JD' : '目标岗位方向' }}</span>
            <el-tag size="small">可入知识库</el-tag>
          </div>
        </template>

        <template v-if="mode === 'jd'">
          <el-input
            v-model="jdText"
            type="textarea"
            :rows="14"
            resize="none"
            placeholder="请粘贴目标公司的岗位 JD。系统会围绕这一个 JD 输出匹配报告，不默认推荐其他公司。"
          />
        </template>

        <template v-else>
          <el-form label-position="top">
            <el-form-item label="目标岗位">
              <el-select v-model="targetDirection" class="full-width">
                <el-option
                  v-for="item in directionOptions"
                  :key="item"
                  :label="item"
                  :value="item"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="经验阶段">
              <el-select v-model="experienceLevel" class="full-width">
                <el-option label="校招 / 实习" value="校招 / 实习" />
                <el-option label="1-3 年" value="1-3 年" />
                <el-option label="3-5 年" value="3-5 年" />
                <el-option label="5 年以上" value="5 年以上" />
              </el-select>
            </el-form-item>

            <div class="job-profile-preview">
              <h3>岗位画像预览</h3>
              <p>
                后续将从 JD 知识库检索同类岗位，聚合核心技能、项目要求、关键词权重和常见加分项。
              </p>
            </div>
          </el-form>
        </template>
      </el-card>
    </section>

    <section class="action-bar">
      <el-button type="primary" size="large" @click="runAnalysis">
        开始分析
      </el-button>
      <el-button size="large">清空输入</el-button>
      <span>当前为前端模拟结果，后续接入 FastAPI 与 LLM Agent 工作流。</span>
    </section>

    <section v-if="hasReport" class="report-grid">
      <el-card shadow="never" class="panel-card score-card">
        <template #header>{{ reportTitle }}</template>
        <div class="score-number">78</div>
        <p>{{ reportDescription }}</p>
      </el-card>

      <el-card shadow="never" class="panel-card">
        <template #header>能力匹配摘要</template>
        <el-progress :percentage="82" />
        <el-progress :percentage="74" status="success" />
        <el-progress :percentage="61" status="warning" />
        <ul class="plain-list">
          <li>核心技能覆盖较好，但项目成果指标需要补充真实评测口径。</li>
          <li>项目描述可进一步突出问题背景、技术方案和可验证结果。</li>
          <li>缺失关键词不直接编造，只提示用户补充真实经历或学习计划。</li>
        </ul>
      </el-card>

      <el-card shadow="never" class="panel-card">
        <template #header>真实性检查</template>
        <el-alert
          title="不生成无法验证的虚假经历或虚假指标"
          type="success"
          :closable="false"
          show-icon
        />
        <ul class="plain-list">
          <li>没有实际数据时，不写“提升 35%”这类具体数值。</li>
          <li>建议先补充测试样本、评测方式、耗时对比，再填写真实结果。</li>
          <li>把“参与”包装成“主导”会被标记为夸大风险。</li>
        </ul>
      </el-card>
    </section>
  </main>
</template>

<style scoped>
.workspace-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 20px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #2563eb;
  font-size: 14px;
  font-weight: 700;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 10px;
  color: #111827;
  font-size: 30px;
  line-height: 1.25;
}

.subtitle {
  margin-bottom: 0;
  color: #667085;
}

.privacy-banner,
.mode-card,
.panel-card,
.action-bar {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
}

.privacy-banner {
  margin-bottom: 18px;
  padding: 14px 16px;
  color: #475467;
}

.mode-card {
  margin-bottom: 18px;
  padding: 18px;
}

.section-title {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 16px;
}

.section-title h2 {
  margin-bottom: 0;
  font-size: 18px;
}

.section-title span {
  color: #667085;
  font-size: 14px;
}

.input-grid,
.report-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.full-width {
  width: 100%;
}

.job-profile-preview {
  min-height: 214px;
  padding: 18px;
  border: 1px dashed #b9c4d3;
  border-radius: 8px;
  background: #f8fafc;
  color: #475467;
}

.job-profile-preview h3 {
  margin-bottom: 8px;
  color: #111827;
  font-size: 16px;
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 18px 0;
  padding: 16px;
}

.action-bar span {
  color: #667085;
  font-size: 14px;
}

.report-grid {
  grid-template-columns: 0.8fr 1.1fr 1.1fr;
}

.score-card p {
  color: #667085;
  line-height: 1.7;
}

.score-number {
  margin-bottom: 8px;
  color: #2563eb;
  font-size: 56px;
  font-weight: 800;
  line-height: 1;
}

.plain-list {
  margin: 14px 0 0;
  padding-left: 18px;
  color: #475467;
  line-height: 1.8;
}

@media (max-width: 900px) {
  .workspace-page {
    padding: 20px;
  }

  .page-header,
  .section-title,
  .action-bar {
    align-items: stretch;
    flex-direction: column;
  }

  .input-grid,
  .report-grid {
    grid-template-columns: 1fr;
  }
}
</style>
