<script setup lang="ts">
import type { CurrentStatus, Forecast } from '~/types/api'

interface Props {
  current: CurrentStatus
  forecast?: Forecast
}

const props = defineProps<Props>()

const occupancyColor = (rate: number) => {
  if (rate >= 90) return 'text-red-600 dark:text-red-400'
  if (rate >= 70) return 'text-orange-600 dark:text-orange-400'
  if (rate >= 50) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-green-600 dark:text-green-400'
}

const occupancyBgColor = (rate: number) => {
  if (rate >= 90) return 'bg-red-100 dark:bg-red-900/20'
  if (rate >= 70) return 'bg-orange-100 dark:bg-orange-900/20'
  if (rate >= 50) return 'bg-yellow-100 dark:bg-yellow-900/20'
  return 'bg-green-100 dark:bg-green-900/20'
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle class="text-lg">{{ current.name }}</CardTitle>
      <CardDescription>Last updated: {{ formatTime(current.timestamp) }}</CardDescription>
    </CardHeader>
    <CardContent>
      <div class="space-y-4">
        <!-- Current Status -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium">Current Occupancy</span>
            <span :class="['text-2xl font-bold', occupancyColor(current.occupancy_rate)]">
              {{ current.occupancy_rate.toFixed(1) }}%
            </span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
            <div 
              :class="['h-2.5 rounded-full', occupancyBgColor(current.occupancy_rate)]"
              :style="{ width: `${current.occupancy_rate}%` }"
            ></div>
          </div>
          <div class="flex justify-between text-xs text-muted-foreground mt-1">
            <span>{{ current.free }} free</span>
            <span>{{ current.total }} total</span>
          </div>
        </div>

        <!-- Forecast -->
        <div v-if="forecast" class="pt-4 border-t">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium flex items-center gap-1">
              <Icon name="lucide:trending-up" class="w-4 h-4" />
              Predicted Occupancy
            </span>
            <span :class="['text-xl font-semibold', occupancyColor(forecast.predicted_occupancy_rate)]">
              {{ forecast.predicted_occupancy_rate.toFixed(1) }}%
            </span>
          </div>
          <div v-if="forecast.confidence_low !== undefined && forecast.confidence_high !== undefined" class="text-xs text-muted-foreground">
            Confidence range: {{ forecast.confidence_low.toFixed(1) }}% - {{ forecast.confidence_high.toFixed(1) }}%
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
