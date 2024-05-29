apply:
	terraform init
	terraform apply -auto-approve

zip-code:
	zip -r lambda_function.zip ./telegram_bot/*
	aws s3 cp lambda_function.zip s3://telegram-bot-lambda-bucket/lambda_function.zip
	terraform apply -auto-approve

zip-layer:
	pip3 install --no-cache-dir -r requirements.txt -t ./python
	zip -r python.zip ./python/*
	aws s3 cp python.zip s3://telegram-bot-lambda-bucket/python.zip
	terraform apply -auto-approve