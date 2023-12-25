import asyncio
import argparse
import src.pipeline.gmail_pipeline as gmail_pipeline

def main():
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Gmail pipeline for a specific company.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    args = parser.parse_args()

    asyncio.run(gmail_pipeline.run_pipeline(args.company.upper()))