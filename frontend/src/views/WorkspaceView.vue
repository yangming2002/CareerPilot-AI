<script setup lang="ts">
import { ref } from 'vue'
import ModuleSelector from '@/components/workspace/ModuleSelector.vue'
import ResumeInputPanel from '@/components/workspace/ResumeInputPanel.vue'
import MatchingPanel from '@/components/workspace/MatchingPanel.vue'
import TrackerPanel from '@/components/workspace/TrackerPanel.vue'
import InterviewPanel from '@/components/workspace/InterviewPanel.vue'
import WrittenTestPanel from '@/components/workspace/WrittenTestPanel.vue'
import SkillProfilePanel from '@/components/workspace/SkillProfilePanel.vue'
import AnalysisReport from '@/components/workspace/AnalysisReport.vue'

const activeModule = ref('matching')
</script>

<template>
  <main class="workspace-page">
    <!-- Header -->
    <section class="page-header">
      <div>
        <p class="eyebrow">CareerPilot-AI</p>
        <h1>面向个人求职全流程的智能工作台</h1>
        <p class="subtitle">
          Agent 驱动 · RAG 记忆增强 · 简历可信优化 · 投递追踪 · 面试/笔试复盘 · 能力画像。
          上传简历和 JD，Agent 自动解析、匹配、校验并生成改写建议，每次分析沉淀为个人求职记忆。
        </p>
      </div>
      <el-tag type="success" effect="light">Agent 驱动</el-tag>
    </section>

    <!-- Privacy Banner -->
    <section class="privacy-banner">
      <strong>产品原则：</strong>
      简历优化不编造经历，LLM 建议必须有原文依据。JD 归档到 RAG 记忆库，下次分析时自动检索相关经历。所有个人数据按敏感数据处理，不默认联网搜索。
    </section>

    <!-- Module Selector -->
    <ModuleSelector v-model="activeModule" />

    <!-- Input Area -->
    <section class="input-grid">
      <ResumeInputPanel />

      <MatchingPanel v-if="activeModule === 'matching'" />
      <TrackerPanel v-else-if="activeModule === 'tracker'" />
      <InterviewPanel v-else-if="activeModule === 'interview'" />
      <WrittenTestPanel v-else-if="activeModule === 'written'" />
      <SkillProfilePanel v-else-if="activeModule === 'profile'" />
    </section>

    <!-- Analysis Report (only for matching module) -->
    <AnalysisReport v-if="activeModule === 'matching'" />
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

.privacy-banner {
  margin-bottom: 18px;
  padding: 14px 16px;
  color: #475467;
  line-height: 1.7;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
}

.input-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.panel-card {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

@media (max-width: 900px) {
  .workspace-page {
    padding: 20px;
  }

  .page-header {
    align-items: stretch;
    flex-direction: column;
  }

  .input-grid {
    grid-template-columns: 1fr;
  }
}
</style>
