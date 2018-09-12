I've task to organize postgres backups for one of our clients.
I've picked Barman as a soultion.
But just "Barman from box" does not provide features i was need and i've decided to make some wrappers for backup and restore.

Wrapper for backup checks for backups every time script is running according backup policy.
Next it removes outdated backup archives from filesystem.
Then he checks if time has come to make another backup. And if it come then he start backup procedure, if not then he stop.
Also it' provised detailed logs of it's work, so it's make debugging way more simple than without it.
