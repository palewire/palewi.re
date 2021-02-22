backupdb:
	heroku pg:backups:capture


downloaddb:
	heroku pg:backups:download


restoredb:
	pg_restore --verbose --clean --no-acl --no-owner -h localhost -U postgres -d palewire latest.dump


loaddb:
	backupdb
	downloaddb
	restoredb
	rm latest.dump
