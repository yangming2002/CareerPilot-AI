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
  <div class="workspace">
    <div class="ws-header">
      <div>
        <h1>简历 & JD 分析</h1>
        <p>Agent 自动解析、匹配、校验并生成改写建议</p>
      </div>
      <ModuleSelector v-model="activeModule" />
    </div>

    <!-- Matching Module -->
    <template v-if="activeModule === 'matching'">
      <div class="ws-grid">
        <ResumeInputPanel />
        <MatchingPanel />
      </div>
      <AnalysisReport />
    </template>

    <!-- Other Modules -->
    <TrackerPanel v-else-if="activeModule === 'tracker'" />
    <InterviewPanel v-else-if="activeModule === 'interview'" />
    <WrittenTestPanel v-else-if="activeModule === 'written'" />
    <SkillProfilePanel v-else-if="activeModule === 'profile'" />
  </div>
</template>

<style scoped>
.workspace { padding: 32px 40px; max-width: 1500px; }

.ws-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 28px;
  gap: 24px;
}

.ws-header h1 { font-size: 24px; font-weight: 700; color: #111827; margin-bottom: 4px; }
.ws-header p { font-size: 14px; color: #6b7280; }

.ws-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 1100px) {
  .workspace { padding: 24px; }
  .ws-grid { grid-template-columns: 1fr; }
  .ws-header { flex-direction: column; }
}
</style>
