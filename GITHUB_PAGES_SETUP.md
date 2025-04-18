# Setting Up GitHub Pages for SmartFill.AI

This guide will help you enable GitHub Pages for your SmartFill.AI repository.

## Steps to Enable GitHub Pages

1. Go to your GitHub repository at https://github.com/zyxcambridge/autofilltable

2. Click on the "Settings" tab at the top of the repository page
   ![Settings Tab](https://docs.github.com/assets/cb-27528/mw-1440/images/help/repository/repo-actions-settings.webp)

3. In the left sidebar, click on "Pages"
   ![Pages Section](https://docs.github.com/assets/cb-47267/mw-1440/images/help/pages/pages-tab.webp)

4. Under "Build and deployment" > "Source", select "Deploy from a branch"

5. Under "Branch", select "main" and "/" (root) folder

   **Important**: Do NOT select the "/docs" folder as this can cause issues with GitHub Pages
   ![Branch Selection](https://docs.github.com/assets/cb-86795/mw-1440/images/help/pages/publishing-source-drop-down.webp)

6. Click "Save"

7. Wait a few minutes for GitHub to build and deploy your site

8. Once deployed, you'll see a message saying "Your site is live at https://zyxcambridge.github.io/autofilltable/"

## Accessing Your GitHub Pages Site

After the site is deployed, you can access it at:

https://zyxcambridge.github.io/autofilltable/

## Updating Your GitHub Pages Site

To update your GitHub Pages site:

1. Make changes to the files in the `docs/` directory
2. Commit and push the changes to GitHub
3. GitHub will automatically rebuild and deploy your site

## Customizing Your Site

You can customize your site by editing the following files:

- `docs/index.html`: The main HTML file
- `docs/css/styles.css`: The CSS styles
- `docs/js/main.js`: JavaScript functionality
- `docs/assets/images/`: Directory for images

## Troubleshooting

If your site doesn't appear after enabling GitHub Pages:

1. Check that you've selected the correct branch and folder (use the root folder "/" NOT "/docs")
2. Ensure that your repository is public
3. Wait a few minutes for GitHub to build and deploy your site
4. Check for any build errors in the GitHub Pages section of your repository settings
5. Make sure the .nojekyll file exists in your repository
6. Try accessing the site directly at https://zyxcambridge.github.io/autofilltable/index.html

## Common Issues

### 404 Error

If you see a "404 There isn't a GitHub Pages site here" error:

1. Make sure you've enabled GitHub Pages in your repository settings
2. Ensure you've selected the main branch and root folder ("/")
3. Check if your repository is public
4. Wait 5-10 minutes for GitHub to build and deploy your site
5. Try clearing your browser cache or using a different browser

### Missing CSS or Images

If your site appears but is missing styles or images:

1. Check that all file paths are correct (they should be relative paths)
2. Ensure all files have been properly committed and pushed to GitHub
3. Check for any console errors in your browser's developer tools
