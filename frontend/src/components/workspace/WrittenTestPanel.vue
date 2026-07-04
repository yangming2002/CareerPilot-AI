<script setup lang="ts">
import { ref } from 'vue'
import { useWrittenTestStore } from '@/stores/writtenTest'
import { ElMessage } from 'element-plus'

const store = useWrittenTestStore()
store.fetchAll()

const company = ref('')
const position = ref('')
const problemType = ref('')
const difficulty = ref('中等')
const solved = ref(false)
const stuckPoint = ref('')
const knowledgeTags = ref('')

const difficultyOptions = ['简单', '中等', '困难']
const problemTypes = ['算法', '数据结构', '系统设计', 'SQL', '逻辑题', '行为题', '专业知识', '其他']

async function submit() {
  if (!company.value.trim()) {
    ElMessage.warning('请填写公司名称')
    return
  }
  const tags = knowledgeTags.value
    .split(/[,;，；]/)
    .map((t) => t.trim())
    .filter(Boolean)

  await store.create({
    company: company.value.trim(),
    position: position.value.trim() || undefined,
    problem_type: problemType.value || undefined,
    difficulty: difficulty.value,
    solved: solved.value,
    stuck_point: stuckPoint.value.trim() || undefined,
    knowledge_tags: tags.length ? tags : undefined,
  })
  company.value = ''
  position.value = ''
  problemType.value = ''
  solved.value = false
  stuckPoint.value = ''
  knowledgeTags.value = ''
  ElMessage.success('笔试复盘已保存')
}
</script>

<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <span>新增笔试复盘</span>
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
        <el-col :span="8">
          <el-form-item label="题目类型">
            <el-select v-model="problemType" class="full-width" clearable>
              <el-option
                v-for="item in problemTypes"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="难度">
            <el-select v-model="difficulty" class="full-width">
              <el-option
                v-for="item in difficultyOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="是否做出">
            <el-switch v-model="solved" active-text="是" inactive-text="否" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="卡住的知识点">
        <el-input
          v-model="stuckPoint"
          type="textarea"
          :rows="3"
          resize="none"
          placeholder="描述卡住的地方或没做出来的原因"
        />
      </el-form-item>
      <el-form-item label="知识标签（逗号分隔）">
        <el-input v-model="knowledgeTags" placeholder="例如：动态规划, BFS, 数据库索引" />
      </el-form-item>
      <el-button type="primary" @click="submit">保存笔试记录</el-button>
    </el-form>
  </el-card>

  <el-card v-if="store.reviews.length" shadow="never" class="panel-card list-card">
    <template #header>
      <div class="card-header">
        <span>笔试记录（{{ store.reviews.length }}）</span>
      </div>
    </template>

    <el-table :data="store.reviews" stripe size="small" style="width: 100%">
      <el-table-column prop="company" label="公司" width="120" />
      <el-table-column prop="problem_type" label="题型" width="90" />
      <el-table-column prop="difficulty" label="难度" width="70" />
      <el-table-column label="做出" width="70">
        <template #default="{ row }">
          <el-tag :type="row.solved ? 'success' : 'danger'" size="small">
            {{ row.solved ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="stuck_point" label="卡住点" min-width="150" />
      <el-table-column label="标签" min-width="150">
        <template #default="{ row }">
          <el-tag
            v-for="tag in row.knowledge_tags"
            :key="tag"
            size="small"
            style="margin-right: 4px"
          >
            {{ tag }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
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
</style>
