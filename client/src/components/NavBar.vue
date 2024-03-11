<script setup lang="ts">
</script>

<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-light">
    <router-link to="/" class="navbar-brand">FilaForge</router-link>

    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>

    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav mr-auto">
        <li class="nav-item">
          <router-link to="/" class="nav-link" active-class="active">Home</router-link>
        </li>
        <li class="nav-item">
          <router-link to="/queue" class="nav-link" active-class="active">Queues</router-link>
        </li>
        <li class="nav-item">
          <router-link to="/registration" class="nav-link" active-class="active">Registration</router-link>
        </li>
        <li class="nav-item">
          <router-link to="/submit" class="nav-link" active-class="active">Submit Job</router-link>
        </li>
        <li class="nav-item">
          <router-link to="/history" class="nav-link" active-class="active">Job History</router-link>
        </li>
      </ul>

      <router-link to="/submit" class="btn btn-outline-success my-2 my-sm-0">Submit Job</router-link>
    </div>
  </nav>
</template>

<style scoped>
.btn{
  margin-right: 3%; 
}

.navbar-brand, .navbar-dropdown{
  margin-left: 2%; 
}

</style>