<script setup lang="ts">
import { ref } from 'vue'
import { useApplicationStore } from '@/stores/application'
import { ElMessage } from 'element-plus'

const store = useApplicationStore()
store.fetchAll()

const company = ref('')
const position = ref('')
const channel = ref('')
const status = ref('待投递')
const notes = ref('')

const statusOptions = [
  '待投递', '已投递', '简历筛选中', '笔试',
  '一面', '二面', '三面', 'HR 面',
  'Offer', '已挂', '已放弃', '冷静期',
]

async function submit() {
  if (!company.value.trim() || !position.value.trim()) {
    ElMessage.warning('请填写公司名称和岗位名称')
    return
  }
  try {
    await store.create({
      company: company.value.trim(),
      position: position.value.trim(),
      channel: channel.value.trim() || undefined,
      status: status.value,
      notes: notes.value.trim() || undefined,
    })
    company.value = ''
    position.value = ''
    channel.value = ''
    status.value = '待投递'
    notes.value = ''
    ElMessage.success('投递记录已保存')
  } catch {
    // Error toast already shown by interceptor
  }
}

async function changeStatus(appId: number, newStatus: string) {
  await store.updateStatus(appId, newStatus)
  ElMessage.success('状态已更新')
}

async function remove(appId: number) {
  await store.remove(appId)
  ElMessage.success('已删除')
}
</script>

<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <span>新增投递记录</span>
      </div>
    </template>

    <el-form label-position="top" size="default">
      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="公司名称">
            <el-input v-model="company" placeholder="例如：某互联网公司" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="岗位名称">
            <el-input v-model="position" placeholder="例如：Agent 开发工程师" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="投递渠道">
            <el-input v-model="channel" placeholder="官网/内推/Boss" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="当前状态">
            <el-select v-model="status" class="full-width">
              <el-option
                v-for="item in statusOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="备注">
            <el-input v-model="notes" placeholder="任意备注" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-button type="primary" @click="submit" style="margin-top: 8px">
        保存投递记录
      </el-button>
    </el-form>
  </el-card>

  <el-card v-if="store.applications.length" shadow="never" class="panel-card list-card">
    <template #header>
      <div class="card-header">
        <span>投递列表（{{ store.applications.length }}）</span>
      </div>
    </template>

    <el-table :data="store.applications" stripe size="small" style="width: 100%">
      <el-table-column prop="company" label="公司" width="140" />
      <el-table-column prop="position" label="岗位" width="140" />
      <el-table-column prop="channel" label="渠道" width="80" />
      <el-table-column label="状态" width="140">
        <template #default="{ row }">
          <el-select
            :model-value="row.status"
            size="small"
            @change="(v: string) => changeStatus(row.id, v)"
          >
            <el-option
              v-for="item in statusOptions"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="notes" label="备注" min-width="120" />
      <el-table-column label="操作" width="70">
        <template #default="{ row }">
          <el-button
            type="danger"
            size="small"
            text
            @click="remove(row.id)"
          >
            删除
          </el-button>
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
