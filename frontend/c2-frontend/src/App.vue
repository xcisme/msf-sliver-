<script setup>
</script>

<template>
  <router-view v-slot="{ Component }">
    <component :is="Component" />
  </router-view>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Microsoft YaHei', 'Source Han Sans CN', sans-serif;
}
</style>
