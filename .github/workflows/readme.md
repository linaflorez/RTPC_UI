## Step-by-step guide for a typical workflow

Here’s how the process works when focused solely on tagging and automated releases:

### Step 1: Make Code Changes

1. **Make your changes locally** in your repository as usual.
2. **Commit your changes**:

   ```bash
   git add .
   git commit -m "Your commit message"
   ```

### Step 2: Push Changes to `main` (or another branch)

1. **Push your changes** to GitHub:

   ```bash
   git push origin main  # or the branch you are working on
   ```

### Step 3: Create and Push a Tag

1. **Create a new tag** (following semantic versioning or your own versioning strategy):

   ```bash
   git tag v1.013  # Replace with your version number, it needs to be unique
   ```

2. **Push the tag to GitHub**:

   ```bash
   git push origin v1.013
   ```

   This step triggers the GitHub Actions workflow associated with that tag. Change the version for every new update you've made and want to release.

### Step 4: Automatic Release Creation

Once the tag is pushed, GitHub Actions will automatically:

1. **Run the configured workflow**.
2. **Build the project**.
3. **Create a release** on GitHub and upload the associated artifacts (e.g., `.zip`, `app`, etc.).

- \* Please note that you don't have to create a release everytime you make a new code change, only when you are finally ready to release something.

### Summary of the Tagging Workflow

- **Commit Changes**: Make and commit your changes as usual.
- **Tag the Commit**: Create a new tag using `git tag`.
- **Push the Tag**: Push the tag to GitHub, which triggers the workflow.
- **Automatic Release**: The GitHub Actions workflow automatically builds your project, creates a release, and uploads the artifact.
