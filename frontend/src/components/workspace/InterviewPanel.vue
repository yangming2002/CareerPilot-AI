<script setup lang="ts">
import { ref } from 'vue'
import { useInterviewStore } from '@/stores/interview'
import { ElMessage } from 'element-plus'

const store = useInterviewStore()
store.fetchAll()

const company = ref('')
const position = ref('')
const round = ref('一面')
const weakPoints = ref('')
const result = ref('')

const roundOptions = ['一面', '二面', '三面', 'HR 面', '终面', '加面']

async function submit() {
  if (!company.value.trim()) {
    ElMessage.warning('请填写公司名称')
    return
  }
  await store.create({
    company: company.value.trim(),
    position: position.value.trim() || undefined,
    round: round.value,
    weak_points: weakPoints.value.trim() || undefined,
    result: result.value || undefined,
  })
  company.value = ''
  position.value = ''
  weakPoints.value = ''
  result.value = ''
  ElMessage.success('面试复盘已保存')
}
</script>

<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <span>新增面试复盘</span>
      </div>
    </template>

    <el-form label-position="top" size="default">
      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="公司">
            <el-input v-model="company" placeholder="公司名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="岗位">
            <el-input v-model="position" placeholder="岗位名称" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="面试轮次">
            <el-select v-model="round" class="full-width">
              <el-option
                v-for="item in roundOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="结果">
            <el-input v-model="result" placeholder="通过/未通过/等待" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="薄弱点 / 没答好的地方">
        <el-input
          v-model="weakPoints"
          type="textarea"
          :rows="5"
          resize="none"
          placeholder="记录面试问题和没答好的地方，系统会生成复盘建议"
        />
      </el-form-item>
      <el-button type="primary" @click="submit">保存复盘记录</el-button>
    </el-form>
  </el-card>

  <el-card v-if="store.reviews.length" shadow="never" class="panel-card list-card">
    <template #header>
      <div class="card-header">
        <span>复盘列表（{{ store.reviews.length }}）</span>
      </div>
    </template>

    <div v-for="r in store.reviews" :key="r.id" class="review-item">
      <div class="review-meta">
        <strong>{{ r.company }}</strong>
        <span v-if="r.position"> · {{ r.position }}</span>
        <el-tag size="small" style="margin-left: 8px">{{ r.round }}</el-tag>
        <el-tag v-if="r.result" size="small" type="warning" style="margin-left: 4px">
          {{ r.result }}
        </el-tag>
      </div>
      <p v-if="r.weak_points" class="review-weak">{{ r.weak_points }}</p>
      <div v-if="r.coaching_suggestions?.length" class="coaching">
        <span class="coaching-label">辅导建议：</span>
        <ul>
          <li v-for="(tip, i) in r.coaching_suggestions" :key="i">{{ tip }}</li>
        </ul>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.panel-card {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
}

.list-card {
  margin-top: 18px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.full-width {
  width: 100%;
}

.review-item {
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.review-item:last-child {
  border-bottom: none;
}

.review-meta {
  margin-bottom: 6px;
  color: #1f2937;
}

.review-weak {
  margin: 4px 0;
  color: #667085;
  font-size: 14px;
  line-height: 1.6;
}

.coaching {
  margin-top: 8px;
  padding: 10px 14px;
  background: #f0f9ff;
  border-radius: 6px;
  font-size: 13px;
}

.coaching-label {
  font-weight: 600;
  color: #2563eb;
}

.coaching ul {
  margin: 4px 0 0;
  padding-left: 18px;
  color: #475467;
}
</style>
