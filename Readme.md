<h1>RSS Harvester</h1>
<h2>Purpose</h2>
RSS Harvester is written as a cyber security  open source intel harvesting utility.  The tool reads a list of RSS feed URLs from a text based CSV file, connects to those feeds, pulls down the articles, and stores them in PANDAS Datafield.  It then uses a ranked keyword list also in text CSV format to train a   machine learning model to evaluate and rank each articles contents based on correlation with the keyword list ranking. 

<h2>Operation</h2>
Ideally this provides a mechanism for flagging articles that are relevant to emerging threats and exploits for an analyst to review for relevance and further research. The keyword list is maintained in Text format to allow analysts to add, remove and adjust the ranking of entries.  This allows new keywords to be added, low value keywords to be deranked and emerging threat words to be escallated over time. 

The URL list can be easily edited to add and remove relevant RSS feed sources.  the included test feed list contains approximately 100 RSS feeds, that typcially produces about 2500 articles.  The tools has been test with URL list as large as 10,000 feeds and is able to parse the list in approximately 6 minutes using 30mbps of bandwidth and producing a list of 20,0000 articles. 

The output  is configurable to save in tab seperated CSV, parquet, pickle and excel formats.  The CSV format can be corrupted by special characters in the feeds, the excel format work well; however articles with more than 32,000 characters in the summary will be truncated. The parquet and pickle formats overcome these issues.  

<h2>Code </h2>
The tool is written and tested using Python 3 (3.10 specifically) and uses Python libraries that include:
- **Feedparser** 
	This library is used to pull and parse the feeds into articles 
- **Urllib** 
	This library is used to format the feed requests, append acceptable user-agent type, and gracefully handle connection exceptions.
- **Pandas**
	This library is used to store, manipulate, analyze, save and load data from the filesystem.
- SpaCy
	This library is used to analyze the articles and rank them using a natural language machine learning training model
- Concurrent
	This library is used to parallelize the process of pulling a large number of feeds into individual processes so that a large quantity of URLs and feed articles can be gathered efficiently. 

<h2>Instructions</h2>
<b>Setup Python</b>		
Install Python 3.10 from the python website ( https://www.python.org/downloads/release/python-3100/ ). 
	<i>NOTE: Installing Python through Microsoft store will result in issues with installed libraries</i>					

Install required libraries using the pip utility. 
	pip install pandas
	pip install feedparser
	pip install nltk
	pip install pyqt5
	pip install turtle
	pip install string
	pip install hashlib
	pip install collections import Counter
	pip install numpy
	pip install spacy
	pip install -U scikit-learn
	pip install pyqt6
	pip install pyarrow
	python -m spacy download en_core_web_md

<b>Setup pip</b>
If pip is not recognized, install pip
	Download PIP get-pip.py
		Launch a command prompt
		Run 
			curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
	Installing PIP
		python get-pip.py

<b>Setup Application</b> 
Download the rss_harvester file folder.  The folder contains the application and supporting configuration data files and sample output files. 

Before running the program double check that all items are located within the same folder.

Run <i>python3 rss_harvester.py</i> 
Once the application is executed progress will be output to the console.  First the URL access and download progress, then the ranking of each article.

The default configuration will save the output to a file named <i>rss_url.csv</i>
The file is organized into 
- Source
- Title
- Summary
- Link
- Score

- Source 
	This column provides the URL that the rss_harvester used to collect the article.
- Title
	This column provides the Title provided by the feed for the article.
- Summary
	This column provides the article primary content.
- Link
	This colum provides a hyperlink to the specific article accessible by browser to support further research
- Score
	This column provides the score produced through correlation with the keyword list ranking. 
	<b><i>NOTE:</i></b> That this is the first iteration of a proof of concept and this scoring component requires further testing, analysis and development
	
