#
# Compare Category and Master files
#

$master = Get-Content .\master.csv | Select-Object -Skip 1
$categories = @(
	Get-Content .\certifications.csv | Select-Object -Skip 1
	Get-Content .\cybersec.csv | Select-Object -Skip 1
	Get-Content .\devsec.csv | Select-Object -Skip 1
	Get-Content .\engineer.csv | Select-Object -Skip 1
	Get-Content .\management.csv | Select-Object -Skip 1
	Get-Content .\standards.csv | Select-Object -Skip 1
)

Compare-Object $categories $master
