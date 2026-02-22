# NSE Quant Tool

A quantitative analysis tool designed for NSE (National Stock Exchange) data.

## Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your machine.
- [Git](https://git-scm.com/downloads) installed.
- A GitHub account.

## Running with Docker

Ensure you have a `Dockerfile` in the root of your project. To run the application using Docker, follow these steps:

1.  **Build the Docker image:**

    Navigate to the project root directory in your terminal and run:

    ```bash
    docker build -t nse-quant-tool .
    ```

2.  **Run the Docker container:**

    Once the image is built, start the container:

    ```bash
    docker run -it --rm nse-quant-tool
    ```

## Uploading to GitHub

To push this existing project to a new GitHub repository:

1.  **Create a repository on GitHub:**
    *   Log in to GitHub and create a new repository.
    *   Name it `nse-quant-tool`.
    *   Do **not** check "Initialize this repository with a README" (since you have this one).

2.  **Push your code:**

    Run the following commands in your project root:

    ```bash
    # Initialize a new git repository
    git init

    # Add files to staging
    git add .

    # Commit the changes
    git commit -m "Initial commit"

    # Add the remote repository (replace <YOUR_USERNAME> with your actual GitHub username)
    git remote add origin https://github.com/<YOUR_USERNAME>/nse-quant-tool.git

    # Push to the main branch
    git branch -M main
    git push -u origin main
    ```