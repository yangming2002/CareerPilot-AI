<script setup lang="ts">
import { computed, ref } from 'vue'
import ModuleSelector from '@/components/workspace/ModuleSelector.vue'
import ResumeInputPanel from '@/components/workspace/ResumeInputPanel.vue'
import MatchingPanel from '@/components/workspace/MatchingPanel.vue'
import TrackerPanel from '@/components/workspace/TrackerPanel.vue'
import InterviewPanel from '@/components/workspace/InterviewPanel.vue'
import WrittenTestPanel from '@/components/workspace/WrittenTestPanel.vue'
import SkillProfilePanel from '@/components/workspace/SkillProfilePanel.vue'
import AnalysisReport from '@/components/workspace/AnalysisReport.vue'

const activeModule = ref('matching')

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
</script>

<template>
  <main class="workspace-page">
    <!-- Header -->
    <section class="page-header">
      <div>
        <p class="eyebrow">CareerPilot-AI</p>
        <h1>面向个人求职全流程的智能工作台</h1>
        <p class="subtitle">
          围绕用户主动提供的 JD，完成简历匹配、可信优化、投递追踪、冷静期提醒、面试/笔试复盘与能力画像沉淀。
        </p>
      </div>
      <el-tag type="success" effect="light">全栈模式</el-tag>
    </section>

    <!-- Privacy Banner -->
    <section class="privacy-banner">
      <strong>产品原则：</strong>
      不默认替用户联网找岗位，不实时硬爬招聘平台；用户提供目标 JD 后，系统做匹配、记录、复盘和辅导。简历与求职记录均按敏感数据处理。
    </section>

    <!-- Module Selector -->
    <ModuleSelector v-model="activeModule" />

    <!-- Input Area -->
    <section class="input-grid">
      <ResumeInputPanel />

      <el-card shadow="never" class="panel-card">
        <template #header>
          <div class="card-header">
            <span>{{ moduleTitle }}</span>
            <el-tag size="small">用户主动记录</el-tag>
          </div>
        </template>

        <MatchingPanel v-if="activeModule === 'matching'" />
        <TrackerPanel v-else-if="activeModule === 'tracker'" />
        <InterviewPanel v-else-if="activeModule === 'interview'" />
        <WrittenTestPanel v-else-if="activeModule === 'written'" />
        <SkillProfilePanel v-else-if="activeModule === 'profile'" />
      </el-card>
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
