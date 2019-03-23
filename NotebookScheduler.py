import os
import sys
import argparse
import fnmatch
import logging
import papermill as pm
from datetime import datetime
import time

# Notebook Scheduler
# ---------------------------------------
# This script helps with the automated processing of Jupyter Notebooks via papermill (https://github.com/nteract/papermill/)



snapshotDir = 'snapshots'

def findFiles(directory, pattern):
    # Lists all files in the specified directory that match the specified pattern
    for filename in os.listdir(directory):
        if fnmatch.fnmatch(filename.lower(), pattern):
            yield os.path.join(directory, filename)

def processNotebooks(notebookDirectory):
    logging.info('Processing ' + notebookDirectory)
    
    # Each time a notebook is processed a snapshot is saved to a snapshot sub-directory
    # This checks the sub-directory exists and creates it if not
    if os.path.isdir(os.path.join(notebookDirectory,snapshotDir)) == False:
        os.mkdir(os.path.join(notebookDirectory,snapshotDir))
    
    for file in findFiles(notebookDirectory, '*.ipynb'):
        try:
            nb = os.path.basename(file)
            
            now = datetime.now()
            
            # Within the snapshot directory, each notebook output is stored in its own sub-directory
            notebookSnapshot = os.path.join(notebookDirectory, snapshotDir, nb.split('.ipynb')[0])
            
            if os.path.isdir(notebookSnapshot) == False:
                os.mkdir(notebookSnapshot)

            # The output will be saved in a timestamp directory (snapshots/notebook/timestamp) 
            runDir = os.path.join(notebookSnapshot, str(now))
            if os.path.isdir(runDir) == False:
                os.mkdir(runDir)

            # The snapshot file includes a timestamp
            output_file = os.path.join(runDir, nb)
            
            # Execute the notebook and save the snapshot
            pm.execute_notebook(
                file,
                output_file,
                parameters=dict(snapshotDir = runDir + os.sep)
            )
        except Exception:
            # If any errors occur with the notebook processing they will be logged to the log file
            logging.exception("Error processing notebook")



if __name__ == '__main__':

    # Ensure we're running in the same directory as the script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Set up logger to display to screen and file
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename='notebooks.log')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

    # Check if the subfolders for notebooks exist, and create them if they don't
    for directory in ['daily','hourly','weekly', 'monthly']:
        if os.path.isdir(directory) == False:
            os.mkdir(directory)

    # Get optional directory passed in via command line. If this is specified, then we just process the requested directory. 
    # This is useful if you're scheduling the processing with an external task scheduler
    # If directory is not specified, then we'll set up our own scheduler and process the tasks

    parser = argparse.ArgumentParser(description = "NotebookScheduler options")
    parser.add_argument("-d", "--directory", help = "Which set of notebooks to process - e.g. hourly", required = False, default = False)
    argument = parser.parse_args()

    if argument.directory:
        # If a directory has been specified, we'll just process that one directory now and exit
        processNotebooks(argument.directory)    

    else:
        # Only require the schedule module if we're using the internal scheduler
        # Install this with pip install schedule
        import schedule

        # If no directory has been specified, schedule the processing and execute
        schedule.every().hour.at(':40').do(processNotebooks, notebookDirectory='hourly')
        schedule.every().day.at('13:15').do(processNotebooks, notebookDirectory='daily')
        schedule.every().sunday.at('13:15').do(processNotebooks, notebookDirectory='weekly')
        schedule.every().month.do(processNotebooks, notebookDirectory='monthly')

        # Run the scheduled tasks
        while True:
            schedule.run_pending()
            time.sleep(1)
