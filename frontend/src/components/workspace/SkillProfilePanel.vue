<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useSkillProfileStore } from '@/stores/skillProfile'

const store = useSkillProfileStore()

onMounted(() => store.fetchProfile())

watch(
  () => store.profile,
  (p) => {
    if (!p) store.fetchProfile()
  },
)
</script>

<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <span>能力画像</span>
        <el-tag size="small" type="success">自动聚合</el-tag>
      </div>
    </template>

    <div v-if="store.loading" class="loading">加载中...</div>

    <template v-else-if="store.profile">
      <div class="stats-row">
        <div class="stat">
          <span class="stat-num">{{ store.profile.total_applications }}</span>
          <span class="stat-label">总投递</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ store.profile.total_interviews }}</span>
          <span class="stat-label">面试复盘</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ store.profile.total_written_tests }}</span>
          <span class="stat-label">笔试记录</span>
        </div>
      </div>

      <div v-if="store.profile.weak_skill_areas.length" class="section">
        <h3>薄弱技能领域</h3>
        <div class="tags">
          <el-tag
            v-for="skill in store.profile.weak_skill_areas"
            :key="skill"
            type="warning"
            style="margin-right: 6px; margin-bottom: 6px"
          >
            {{ skill }}
          </el-tag>
        </div>
      </div>

      <div v-if="store.profile.interview_weak_points_summary.length" class="section">
        <h3>面试薄弱点</h3>
        <ul class="weak-list">
          <li
            v-for="(point, i) in store.profile.interview_weak_points_summary"
            :key="i"
          >
            {{ point }}
          </li>
        </ul>
      </div>

      <div v-if="store.profile.recent_suggestions.length" class="section">
        <h3>近期建议</h3>
        <ul class="suggest-list">
          <li v-for="(s, i) in store.profile.recent_suggestions" :key="i">
            {{ s }}
          </li>
        </ul>
      </div>

      <div
        v-if="
          !store.profile.weak_skill_areas.length &&
          !store.profile.interview_weak_points_summary.length
        "
        class="empty"
      >
        <p>暂无足够的分析数据来生成能力画像。</p>
        <p>完成 JD 匹配分析和面试复盘后，系统会自动聚合你的技能强项和薄弱点。</p>
      </div>
    </template>

    <div v-else class="empty">
      <p>加载能力画像失败，请确认后端服务已启动。</p>
    </div>
  </el-card>
</template>

<style scoped>
.panel-card {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #667085;
}

.stats-row {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 24px;
  background: #f0f6ff;
  border-radius: 8px;
}

.stat-num {
  font-size: 32px;
  font-weight: 800;
  color: #2563eb;
}

.stat-label {
  color: #667085;
  font-size: 13px;
  margin-top: 4px;
}

.section {
  margin-top: 18px;
}

.section h3 {
  margin-bottom: 10px;
  font-size: 15px;
  color: #1f2937;
}

.tags {
  display: flex;
  flex-wrap: wrap;
}

.weak-list,
.suggest-list {
  margin: 0;
  padding-left: 18px;
  color: #475467;
  line-height: 1.8;
}

.empty {
  padding: 30px;
  text-align: center;
  color: #667085;
  line-height: 1.8;
}
</style>
