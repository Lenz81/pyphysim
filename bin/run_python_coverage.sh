# Example in http://nedbatchelder.com/code/coverage/cmd.html

# You need to install the python-coverage package (available in the Ubuntu
# repositories) to run this script.

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# This script run python-coverage on each test file here and append the
# data to the .coverage file. Then it generates a coverage report.
# 
# Note that the coverage report omits stuff on the /usr folder to avoid
# reporting information about built-in modules.
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Observation: Ideally it is better to run python-coverage on a single test
# file and generate the report only for that test file. In the report one
# would care only about the coverage of the tested module.
#
# That is because the way it is done here (accumulating coverage data from
# all test files) may not spot some methods that are not properly tested
# simple because they are used in other test files.
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Remove any previous information from coverage.
rm .coverage

cd ../tests
for file in *test.py;
do
    echo "xxxxxxxxxx Running python-coverage on file $file"
    python-coverage run -a --omit "/usr/*" $file > /dev/null;
    echo "xxxxxxxxxx Done xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
done

# Generate the report
echo "xxxxxxxxxx Creating Coverage Report xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
python-coverage -rm --omit "/usr/*,/*apps/*","/*__init__*","/*setup.*"
echo "xxxxxxxxxx Done xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


# Note: Test coverage measured over running a whole unit test suite is not
# necessarily a good idea. Measuring a whole run means some things get
# marked as being tested even though they just happen to get called, and
# get called only in some particular way. That means that maybe you should
# run the coverage and the report on each test *.test file instead of
# appending all of the coverage data to the same .coverage file for latter
# report.