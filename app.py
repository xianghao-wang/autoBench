from bench import bench
import sys

if __name__ == '__main__':
    b = bench(sys.argv[1])
    b.store(b.benchAll())