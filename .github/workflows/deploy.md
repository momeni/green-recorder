name: Production deploy
on:
  workflow_run:
    workflows: ["Build Packages"]
    types:
      - completed
  release:
    types: [published]      

jobs:
  job1:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    steps:
      - name: Test
        run: echo Testy