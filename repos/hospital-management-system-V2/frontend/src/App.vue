<template>
  <div id="app">
    <router-view />
    <CustomDialog />
  </div>
</template>

<script>
import CustomDialog from './components/ui/CustomDialog.vue'

export default {
  name: 'App',
  components: { CustomDialog }
}
</script>

<style>
/* Global styles will be in main.css */
</style>
