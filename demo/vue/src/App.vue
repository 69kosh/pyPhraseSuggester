<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <v-layout>
    <v-app-bar title="Phrase Suggester Demo"></v-app-bar>
    <v-main  style="min-height: 300px"><RouterView /></v-main>
  </v-layout>
</template>

<style scoped></style>
