from bench import bench

if __name__ == '__main__':
    config = input("Please enter your benchmark configuration path: ")
    b = bench(config)
    b.store(b.benchAll())