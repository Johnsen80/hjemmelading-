# Troubleshooting

## App will not start
- Reboot and try again.
- Use Help -> Open Logs Folder and review the latest log.
- If a Qt plugin error appears, reinstall the app or rebuild the package.

## Database not found
- Confirm your project folder is accessible.
- Ensure data/reloading.db exists inside the project.
- If the file is missing, restore from backup or Export Pack.

## Import errors
- Validate CSV headers and units.
- Check GRT XML files for missing required fields.
- Review error messages for row numbers and fields.

## Export Pack missing data
- Confirm the current project is set.
- Ensure sessions exist in the database.
- Review logs for export errors.

## Performance issues
- Close unused tabs and restart the app.
- Archive older projects to reduce database size.
- Avoid running heavy workflows simultaneously.

## Where to find logs
- Use Help -> Open Logs Folder.
- Include logs when reporting issues.
