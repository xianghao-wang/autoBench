import csv
import json
import re
import os
import subprocess

# Indexing JSON dictionary
APP_PATH = 'app_path'
BENCH_PATH = 'bench_path'
RESULT_PATH = 'result_path'
TOOLCHAIN = 'toolchain'
TOOL = 'tool'
ENVS = 'envs'
ARGS = 'args'
GREPS = 'greps'

# Regex
TOOL_INDEX_RE = '\d+'

# Represent a tool in the tool chain
class Tool:
    def __init__(self, command ,commonEnvs, commonArgs, greps):
        self.command = command
        self.commonEnvs = commonEnvs
        self.commonArgs = commonArgs
        self.greps = greps

    # Grep result
    def grepResult(self, output):
        result = {}
        for grep in self.greps:
            result[grep] = re.search(self.greps[grep], output).group(1)
        return result

    # Run the tool with given environments and arguments
    def run(self, appPath, envs, args):
        _envs = {**self.commonEnvs, **envs}
        _args = {**self.commonArgs, **args}
        
        # Build environments
        envs = {**dict(os.environ), **_envs}
        # Build arguments
        args = []
        for key, val in _args.items():
            if val is None:
                args.append(f'{key}')
            else:
                val = f'"{val}"' if type(val) == str else f'{val}'
                args.append(f'{key}={val}')
        
        task = subprocess.run([self.command] + args, cwd=appPath, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self.grepResult(task.stdout.decode('utf-8'))

class bench:   
    def __init__(self, config):
        # Read config file
        with open(config, 'r') as f:
            config = json.load(f)
        
        # Application path
        self.appPath = config[APP_PATH]
        # Path for storing result
        self.resultPath = config[RESULT_PATH]
        # Result header
        self.resultHeader = []
        # Toolchain
        self.toolchain = [None] * len(config[TOOLCHAIN])
        for idx in config[TOOLCHAIN]:
            self.toolchain[int(idx)] = Tool(
                config[TOOLCHAIN][idx][TOOL],
                config[TOOLCHAIN][idx][ENVS],
                config[TOOLCHAIN][idx][ARGS],
                config[TOOLCHAIN][idx][GREPS]
            )
            self.resultHeader.extend(config[TOOLCHAIN][idx][GREPS].keys())

        # Import benchmark tasks
        self.tasks = []
        self._rawBench = []
        with open(config[BENCH_PATH], 'r') as f:
            csvObj = csv.DictReader(f)
            for row in csvObj:
                self._rawBench.append(row)
                task = [None] * len(self.toolchain)
                for i in range(len(task)):
                    task[i] = ({}, {}) # (envs, args)
                for col in row:
                    toolIdx = int(re.search(TOOL_INDEX_RE, col).group(0))
                    if col[0] == '$':
                        task[toolIdx][0][col[3:]] = row[col]
                    else:
                        task[toolIdx][1][col[2:]] = row[col]
                self.tasks.append(task)    
    
    def benchAll(self):
        results = []
        for i, task in enumerate(self.tasks):
            print(f'Benchmarking task {i + 1} out of {len(self.tasks)}...')
            result = {}
            for idx, tool in enumerate(self.toolchain):
                result = {**result, **tool.run(self.appPath, task[idx][0], task[idx][1])}
            results.append(result)
        return results
    
    def store(self, results):
        with open(self.resultPath, 'w') as f:
            csvWriter = csv.DictWriter(f, list(self._rawBench[0].keys()) + self.resultHeader)
            csvWriter.writeheader()
            for i, result in enumerate(results):
                csvWriter.writerow({**self._rawBench[i], **result})
        print(f'Written results into {self.resultPath}')
    