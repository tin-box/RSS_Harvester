import concurrent.futures
import urllib.request                                                     
import pandas as pd                                             # pip install pandas
import feedparser                                               # pip install feedparser             
import spacy                                                    # pip install spacy
from sklearn import svm                                         # pip install sklearn
from datetime import datetime
import time
import random

start = time.perf_counter()                                     # Mark start of run to check runtime performance
url_file = 'url_list_short.csv'                                 # Good URLs the harvest culled from the 10K list ulsYYMMDDHHMM.csv
#keyword_list = pd.read_parquet('keyword_list_rank.parquet')     # Keyword list to load that is used for identifying and ranking leads
keyword_list = pd.read_csv('keyword_list_rank.csv',)     # Keyword list to load that is used for identifying and ranking leads
nlp = spacy.load('en_core_web_md')                              # python -m spacy download en_core_web_md  # This is a precompiled word vector map for english
file_prefix = 'rss_urls'                                        # String filename when saving the final RSS Feeds to xlsx file harvested 
workers = 50                                                    # Config how many Threadpool workers to let run, 50 barely touches 8 core, uses about 3GB mem and 30Mbps download                         

def load_urls(urls):                                            # Function to load URLs to use from csv file in same directory NOTE: First line MUST be 'RSSURL'
    return pd.read_csv(urls, index_col=None)['RSSURL']          # Return the parsed URL list to Main to feed the harvester

def get_feed(url, timeout = 60):                                # Function to pull the URL sent, timeout set so the attempt will quit on bad connections
    user_agent = ['Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
                  'Mozilla/5.0 (X11;FreeBSD amd64; rv:105.0) Gecko/20100101 Firefox/105.0',
                  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56',
                  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
                  'Mozilla/5.0(X11;Linux x86_64;rv:105.0)Gecko/20100101 Firefox/105.0'] # List of user agent types to alternate through to get past stingy servers that don't want people like us around
    print(' Get feed URL: ' + url)                              # Give me some feedback so I know whats URL your working on
    req = urllib.request.Request(                               # Fool filters by prescribing a well formed request 
        url,
        data=None,
        headers={
            'User-Agent': random.choice(user_agent)            # Feed them an acceptable user agent from so they don't reject us for being a robot
        }
    )
    return urllib.request.urlopen(req, timeout=timeout).read()  # Send the request, read the reply and return that to Main

def parse(url):                                                 # Function that parses the raw downloaded feed into a format that can be manipulated and analyzed 
    return get_articles(url, (feedparser.parse(get_feed(url, timeout = 60))))

def get_articles(url, parsed):                                  # Breakdown the retrieved feeds that are nested into a flat list of Articles for analysis                                 
    fd = pd.DataFrame(columns = ['source', 'title', 'summary', 'link', 'score'])    # Instantiate the DataFrame with predefined data columns
    articles = {}                                               # Instantiate a Dictionary this is a good approach for building data structures to save in Pandas DataFrames
    entries = parsed['entries']                                 # Simplify the extraction of nested feed data from the 'entries' field
    for entry in entries:                                       # Iterate through the data feed by row
        articles = {                                            # save the Rows relevant data into defined fields
            'source': [url],                                    # The URL that we pulled the feed from 
            'title': [entry['title']],                          # The Title of the Rows Article
            'summary': [entry['summary']],                      # The rows article summary this should be the primary source of leads
            'link': [entry['link']],
            'score': [0]                                        # create a field that can later store an analysis score ranking
        }
        fd = pd.concat([pd.DataFrame(articles),fd], ignore_index=True)  # add the saved row to a Pandas DataFrame
    return fd                                                   # Return the aggregated DataFrame

def iterData(data):                                             # Function to iterate through datasets ... sure I know there are existing standardized solutions but my attention span demanded that I write this and move on 
    output = []                                                 # Instantiate a list to hold our results
    for d in data:                                              # Iterate through the input
        output.append(d)                                        # append the items to the lst
    return output                                               # send the list back from whence it came

def trainWordVector(keyword_list):                              # Initialize and train our Vectorized Word data against our keyword list
    train_x = iterData(keyword_list['keyword'])                 # Push our Keyword list into the training x axis
    train_y = iterData(keyword_list['priority'])                # Push the Keyword priority definitions into the y axis

    train_x_wv = [x.vector for x in [nlp(text) for text in train_x]]    # Create a Word Vector training set with our X axis Keywords 
    svm_wv = svm.SVC(kernel='linear')                       # Instantiate a Word Vector Support Vector Machine object
    return svm_wv.fit(train_x_wv, train_y)                  # use the Support Vector Machine to correlate the keyword axis against the priority ranking axis and return the result 

def rankfeed(rank):                                             # Quick lookup table to numerically categorize the rankings that the Word Vectorization analysis produced.  
    if rank == 'AlertOne':
        return int(1)
    elif rank == 'AlertTwo':
        return int(2)
    elif rank == 'AlertThree':
        return int(3)
    elif rank == 'AlertFour':
        return int(4)    
    elif rank == 'AlertFive':
        return int(5)
    else:
        return int(0)
    
def evalFeed(keyword_list, df):                                 # Main Feed analysis function that uses word vectors to assign a threat priority using a model trained with our keyword list
    clf_svm_wv = trainWordVector(keyword_list)                  # Initialize and train the model
    for d in df.index:                                          # Iterate through our Feed dataset for analysis 
        test_x = [str(df['title'][d]) + ' ' + str(df['summary'][d])]    # Concat the feed rows Title and Summary fields together for analysis

        wv_words = [nlp(text) for text in test_x]               # Incorporate the rows words into a SpaCy Natural Language Processing object
        x_word_vectors = [x.vector for x in wv_words]           # Iterate throug the words and create the X word vectors, frankly this stuff if magic I'm just hitchhiking on the sklearn and spacy libraries

        df.at[d,'score'] = rankfeed(clf_svm_wv.predict(x_word_vectors)[0])  # With the trained NLP model predict the threat ranking and save the ranking to the datafield row score location
        print(str(d) + '\t' + str(df['score'][d]) + '\t' + str(df['source'][d] + '\t' + str(df['title'][d])))   # Give us some console feedback so we know its working 

def saveData(name, df, type):                                   # Function to save our work to a file for posterity
    now = datetime.now()                                        # Get the current time to use in the filename so we know when it was created CM baby!       
    if type == 'xt':                                            # Hey you want an Excel file SURE!
        datafile = name + now.strftime("%y%m%d%H%M") +'.xlsx'   # Assemble the filename  
        df.to_excel((datafile), sheet_name= str(name + '_data'))# Actually save the file using Pandas to_excel method    
    elif type == 'ct':    
        datafile = name + now.strftime("%y%m%d%H%M") +'.csv'    # Assemble the filename  # Hey you want a CSV file SURE!
        df.to_csv((datafile), index=False)                      # Save the file using Pandas to_csv method 
    elif type == 'x':     
        datafile = name +'.xlsx'                                # Assemble the filename  # Hey you want an Excel file SURE!
        df.to_excel((datafile), sheet_name= str(name + '_data'))# Actually save the file using Pandas to_excel method    
    elif type == 'c':                                           # Hey you want a CSV file SURE!
        datafile = name +'.csv'                                 # Assemble the filename  
        df.to_csv((datafile), index=False, sep ='\t')                      # Save the file using Pandas to_csv method     
    elif type == 'p':                                           # Hey you want a Pickle file SURE!
        datafile = name +'.pickle'                              # Assemble the filename  
        df.to_pickle(datafile)                   # Save the file using Pandas to_pickle method   
    elif type == 'pq':                                          # Hey you want a Parquet file SURE! pip install pyarrow
        datafile = name +'.parquet'                              # Assemble the filename  
        df.to_parquet(datafile)                   # Save the file using Pandas to_pickle method 
    else:
        print("Error saving")                                   # Let me know if it failed with bad input
    print("Saving " + name + " data to: ", datafile)            # Let me know that your saving and what the details are that were used
    
def harvData():                                                 # Data harvesting function
    feed = pd.DataFrame()                                       # Instantiate a Pandas Dataframe to store the rss feeds 
    rss_urls = load_urls(url_file)                              # Call the function to load the candidate URLs to be harvested and save the list to rss_urls
    print('Loaded URLs')
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as urlpool:   # Create a Pool of threads so we can get this job done today
        threaded_url = {urlpool.submit(parse, url): url for url in rss_urls}
        for f in concurrent.futures.as_completed(threaded_url): # As threads are completed collect them and process the resulting feed data
            url = threaded_url[f]                               # collect the url that was used because with this threading it doesn't come in a serial manner
            try:
                feed = pd.concat([f.result(),feed], ignore_index=True)  # Add the downloaded feed to the collected Pandas Dataframe
            except Exception as exc:
                print('%r threw an exception: %s' % (url, exc)) # Give us some useful info on exception when servers aren't cooperative
            else:
                print('%r feed was %d bytes' % (url, len(f.result())))  
    return feed

pulled_feed = harvData()
evalFeed(keyword_list, pulled_feed)
finish = time.perf_counter()                                    # Stop the timer and figure out how long it took to run this harvest

saveData(file_prefix, pulled_feed, 'c')                         # Ok save the result to file for analysis c = csv, x = xlsx, xt or ct = filename with save time
saveData(file_prefix, pulled_feed, 'pq')    
print(f'Finished harvest in {round(finish-start, 2)} seconds(s)') # Ready set Stop
print('Pulled ' + str(len(pulled_feed)) + ' feed lines')        # What was our catch?