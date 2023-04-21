<template>
  <v-card class="ma-10">
    <v-card-title>Description</v-card-title>
    <v-card-text>
      Start typing and auto-suggest will show the appropriate options. After typing the
      phrase, and leaving the focus of the field (on blur), the phrase will be sent,
      processed and added to the prompts. Also, the added phrase will be displayed in the
      list under the input field.
    </v-card-text>
  </v-card>
  <v-combobox
    :items="items"
    v-model="text"
    v-on:blur="onBlur"
    no-filter
    class="px-10"
    label="Text field"
    placeholder="Start typing"
    clearable
  ></v-combobox>

  <v-card class="mx-10 mt-5">
    <v-card-title>Added phrases</v-card-title>
    <v-list :items="phrases" item-props lines="one"></v-list>
  </v-card>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
const API_HOST = process.env.VUE_APP_API_HOST;
const API_FETCH_URL = `${API_HOST}/?limit=6&phrase=`;
const API_ADD_URL = `${API_HOST}/add?phrase=`;
const items = ref([]);
const text = ref(null);
const phrases = ref([] as Array<any>);

function onBlur() {
  if (text.value) {
    let url = `${API_ADD_URL}${text.value}`;
    fetch(url, { method: "POST" });
    let now = new Date();
    let rec = { title: text.value, subtitle: now.toLocaleString() };
    phrases.value.unshift(rec);
  }
}

async function fetchItems() {
  let phrase = (text.value || "").toString();
  let url = `${API_FETCH_URL}${phrase}`;
  items.value = await (await fetch(url)).json();
}

watch(text, fetchItems);
fetchItems();
</script>
