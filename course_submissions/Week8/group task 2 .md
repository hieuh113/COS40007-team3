Applied Project Task 2: Implement a GitHub Actions Trigger
Due Sunday by 23:59 Points 20 Submitting a file upload File types pdf, docx, and doc Available until 12 Nov at 23:59
Submission Requirements:

A PDF detailing Studio Activity 7Download Studio Activity 7.  The best way is to include screenshots that show the address bar showing your group number for each point in the rubric. 
Simply copy the Rubric heading and add screenshots.
The model.py file should be your project file that needs to run. This assignment is to create a basic infrastructure that mimics a pipeline. Don't make it complicated.
Integrate the above group task into the Groups GitHub repository. Share the link in the submission.
No GenAI declaration needed.
Rubric
Group Task 2
Group Task 2
Criteria	Ratings	Pts
This criterion is linked to a learning outcomeRepository & File Structure
2 Pts
Excellent
The repository contains the exact required structure: .github/workflows/train.yml, model.py, and requirements.txt. All files are in the correct root or nested directories as specified.
1 Pts
Very good
Repository structure is mostly correct but has a minor error (e.g., the .github folder is named incorrectly, and train.yml is in the wrong directory).
0 Pts
Unsatisfactory
Repository is missing required files or the structure is completely incorrect (e.g., no .github folder, missing model.py). OR Not Done by the group.
2 pts
This criterion is linked to a learning outcomerequirements.txt
2 Pts
Excellent
File includes all necessary libraries (tensorflow, numpy, matplotlib) with correct syntax. Version pinning is logical if used.
1 Pts
Very good
File exists but is missing a required library OR has a typo that would cause installation failure (e.g., tensrflow).
0 Pts
Unsatisfactory
File is missing, empty, or contains invalid package names that would crash the pipeline.
2 pts
This criterion is linked to a learning outcomeWorkflow Triggers (on:)
2 Pts
Excellent
train.yml correctly includes push to main, pull_request to main, AND workflow_dispatch.
1 Pts
Very good
Includes push and pull_request, but missing workflow_dispatch OR triggers are misconfigured (e.g., wrong branch name).
0 Pts
Unsatisfactory
No trigger conditions defined OR triggers are completely incorrect.
2 pts
This criterion is linked to a learning outcomePipeline Job Definition
3 to >2.0 Pts
Excellent
Defines a job named train running on ubuntu-latest with all required sequential steps (checkout, setup-python, cache, install, run, upload).
2 to >1.0 Pts
Very good
The job is defined but is missing 1-2 minor elements (e.g., a cache step or the wrong dependency).
1 to >0 Pts
Unsatisfactory
Job is missing, has no steps, or uses an incorrect runner (e.g., windows-latest without justification).
3 pts
This criterion is linked to a learning outcomeSuccessful Pipeline Execution
4 to >2.0 Pts
Excellent
Pipeline runs to completion without errors on GitHub Actions. All steps (checkout, setup, install, training) show green checkmarks.
2 to >1.0 Pts
Very good
Pipeline runs but fails on a non-critical step (e.g., a cache warning) and still produces artefacts. OR runs successfully only after minor debugging.
1 to >0 Pts
Unsatisfactory
Pipeline fails critically (e.g., dependency install fails, model.py crashes) and produces no output.
4 pts
This criterion is linked to a learning outcomeArtefact Generation & Upload
3 to >2.0 Pts
Excellent
Pipeline successfully generates a results file, like for e.g. model_results.png and metrics.txt via model.py (your project file), and correctly uploads both using actions/upload-artifact@v4.
2 to >1.0 Pts
Very good
Only one of the two expected files is generated/uploaded, or the upload step exists but is misconfigured.
1 to >0 Pts
Unsatisfactory
No artefacts are generated or uploaded. Upload step missing from YAML.
3 pts
This criterion is linked to a learning outcomeDemonstration of Functionality
3 to >2.0 Pts
Excellent
A student can successfully trigger the pipeline via git push, locate the run in GitHub Actions UI, and download artefacts.
2 to >1.0 Pts
Very good
The student can trigger the pipeline but struggles to locate/find artefacts in the UI, or requires assistance.
1 to >0 Pts
Unsatisfactory
The student cannot demonstrate any part of the pipeline workflow or cannot access results.
3 pts
This criterion is linked to a learning outcomeGitHub Link
1 Pts
Satisfactory
GitHub Link provided.
0 Pts
Not Satisfactory
GitHub Link not provided.
1 pts
Total points: 20
