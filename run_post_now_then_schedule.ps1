# Post one image now, then run on schedule. Use this if python is given wrong path.
Set-Location $PSScriptRoot
& "C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe" "test_image_post_then_schedule.py" @args
