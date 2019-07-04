pipenv run python manage.py test users.test -v 2 2> .circleci/test_output.log
sed -e '1,10d' < .circleci/test_output.log  >> .circleci/test_report.log
pipenv run python manage.py test crm.test -v 2 2> .circleci/test_output.log
sed -e '1,10d' < .circleci/test_output.log  >> .circleci/test_report.log
pipenv run python manage.py test questionnaire.test -v 2 2> .circleci/test_output.log
sed -e '1,10d' < .circleci/test_output.log  >> .circleci/test_report.log
pipenv run python manage.py test sales.test -v 2 2> .circleci/test_output.log
sed -e '1,10d' < .circleci/test_output.log  >> .circleci/test_report.log
pipenv run python manage.py send_report
