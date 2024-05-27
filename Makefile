full-deploy:
	pip3 install -r requirements.txt -t .
	zip -r lambda_function.zip .
	terraform init
	terraform apply -auto-approve
zip-deploy:
	zip -r lambda_function.zip .
	terraform apply -auto-approve