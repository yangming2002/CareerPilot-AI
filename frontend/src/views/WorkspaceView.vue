<script setup lang="ts">
import { computed, ref } from 'vue'

const activeModule = ref('matching')
const resumeText = ref('')
const jdText = ref('')
const companyName = ref('')
const positionName = ref('')
const applicationStatus = ref('已投递')
const weakPoint = ref('')
const hasReport = ref(false)

const statusOptions = [
  '待投递',
  '已投递',
  '简历筛选中',
  '笔试',
  '一面',
  '二面',
  '三面',
  'HR 面',
  'Offer',
  '已挂',
  '已放弃',
  '冷静期',
]

const moduleTitle = computed(() => {
  const titles: Record<string, string> = {
    matching: 'JD 匹配分析',
    tracker: '投递进度 Tracker',
    interview: '面试复盘',
    written: '笔试复盘',
    profile: '能力画像',
  }

  return titles[activeModule.value]
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
        <h1>面向个人求职全流程的智能工作台</h1>
        <p class="subtitle">
          围绕用户主动提供的 JD，完成简历匹配、可信优化、投递追踪、冷静期提醒、面试/笔试复盘与能力画像沉淀。
        </p>
      </div>
      <el-tag type="success" effect="light">Frontend Preview</el-tag>
    </section>

    <section class="privacy-banner">
      <strong>产品原则：</strong>
      不默认替用户联网找岗位，不实时硬爬招聘平台；用户提供目标 JD 后，系统做匹配、记录、复盘和辅导。简历与求职记录均按敏感数据处理。
    </section>

    <section class="module-card">
      <div class="section-title">
        <h2>工作台模块</h2>
        <span>先跑通求职闭环，再逐步接入后端 Agent 工作流。</span>
      </div>

      <el-radio-group v-model="activeModule">
        <el-radio-button label="matching">JD 匹配</el-radio-button>
        <el-radio-button label="tracker">投递 Tracker</el-radio-button>
        <el-radio-button label="interview">面试复盘</el-radio-button>
        <el-radio-button label="written">笔试复盘</el-radio-button>
        <el-radio-button label="profile">能力画像</el-radio-button>
      </el-radio-group>
    </section>

    <section class="input-grid">
      <el-card shadow="never" class="panel-card">
        <template #header>
          <div class="card-header">
            <span>简历内容</span>
            <el-tag size="small" type="warning">敏感数据</el-tag>
          </div>
        </template>

        <el-input
          v-model="resumeText"
          type="textarea"
          :rows="12"
          resize="none"
          placeholder="请粘贴简历文本。后端接入后，简历默认只用于本次分析，不写入公共知识库。"
        />
      </el-card>

      <el-card shadow="never" class="panel-card">
        <template #header>
          <div class="card-header">
            <span>{{ moduleTitle }}</span>
            <el-tag size="small">用户主动记录</el-tag>
          </div>
        </template>

        <template v-if="activeModule === 'matching'">
          <el-input
            v-model="jdText"
            type="textarea"
            :rows="12"
            resize="none"
            placeholder="请粘贴你真正想投递的公司 JD。系统围绕该 JD 输出匹配报告，不默认联网搜索或编造岗位信息。"
          />
        </template>

        <template v-else-if="activeModule === 'tracker'">
          <el-form label-position="top">
            <el-form-item label="公司名称">
              <el-input v-model="companyName" placeholder="例如：某互联网公司" />
            </el-form-item>
            <el-form-item label="岗位名称">
              <el-input v-model="positionName" placeholder="例如：Agent 开发工程师" />
            </el-form-item>
            <el-form-item label="当前状态">
              <el-select v-model="applicationStatus" class="full-width">
                <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-form>
        </template>

        <template v-else-if="activeModule === 'interview'">
          <el-input
            v-model="weakPoint"
            type="textarea"
            :rows="12"
            resize="none"
            placeholder="记录面试问题、自己没答好的地方、被追问的问题。系统后续会生成复盘建议和模拟追问。"
          />
        </template>

        <template v-else-if="activeModule === 'written'">
          <el-input
            v-model="weakPoint"
            type="textarea"
            :rows="12"
            resize="none"
            placeholder="记录笔试题型、没做出来的题、卡住的知识点。后续可生成短板图表和刷题建议。"
          />
        </template>

        <template v-else>
          <div class="profile-preview">
            <h3>能力画像预览</h3>
            <p>能力画像会综合 JD 缺口、简历问题、面试反馈和笔试表现，标注主要短板和下一步准备重点。</p>
            <div class="skill-bars">
              <span>项目表达</span><el-progress :percentage="76" />
              <span>算法基础</span><el-progress :percentage="58" status="warning" />
              <span>面试表达</span><el-progress :percentage="64" />
            </div>
          </div>
        </template>
      </el-card>
    </section>

    <section class="action-bar">
      <el-button type="primary" size="large" @click="runAnalysis">生成模拟分析</el-button>
      <el-button size="large">保存记录</el-button>
      <span>当前为前端预览，后续接入 FastAPI、数据库和 LLM 工作流。</span>
    </section>

    <section v-if="hasReport" class="report-grid">
      <el-card shadow="never" class="panel-card score-card">
        <template #header>求职闭环概览</template>
        <div class="score-number">78</div>
        <p>当前简历与目标 JD 匹配度较好，但项目指标、面试表达和笔试短板需要持续记录和复盘。</p>
      </el-card>

      <el-card shadow="never" class="panel-card">
        <template #header>系统建议</template>
        <ul class="plain-list">
          <li>先围绕目标 JD 优化简历关键词和项目表达。</li>
          <li>每次投递记录公司、岗位、简历版本和当前状态。</li>
          <li>面试后立刻记录问题和没答好的地方，避免遗忘。</li>
          <li>笔试题按知识点打标签，积累后生成能力短板图。</li>
        </ul>
      </el-card>

      <el-card shadow="never" class="panel-card">
        <template #header>真实性与隐私</template>
        <el-alert
          title="只优化真实经历，不编造项目、指标、公司或技能"
          type="success"
          :closable="false"
          show-icon
        />
        <ul class="plain-list">
          <li>缺少数据时提示补充真实评测，而不是生成虚假数字。</li>
          <li>投递记录和面试复盘属于个人敏感数据，需要用户授权后才持久化。</li>
          <li>冷静期提醒基于用户自己的投递历史，不依赖不稳定的实时爬虫。</li>
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
  max-width: 860px;
  margin-bottom: 0;
  color: #667085;
  line-height: 1.7;
}

.privacy-banner,
.module-card,
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
  line-height: 1.7;
}

.module-card {
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

.profile-preview {
  min-height: 267px;
  padding: 18px;
  border: 1px dashed #b9c4d3;
  border-radius: 8px;
  background: #f8fafc;
  color: #475467;
}

.profile-preview h3 {
  margin-bottom: 8px;
  color: #111827;
  font-size: 16px;
}

.skill-bars {
  display: grid;
  gap: 10px;
  margin-top: 18px;
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