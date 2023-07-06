# ************************************************************************************************************ Libraries
import snscrape.modules.twitter as sntwitter
import pandas as pd
import requests
import time
import os


# ***************************************************************************************************** Helper Functions


def checkScrapDictionary():
    path = os.getcwd() + "\\scraped_data"
    if not os.path.exists(path):
        os.makedirs(path)


def checkQueryDictionary(username):
    path = os.getcwd() + f"\\scraped_data\\{username}"
    if not os.path.exists(path):
        os.makedirs(path)


def getUserList():
    path = os.getcwd() + f"\\scraped_data\\query_list.txt"
    if not os.path.exists(path):
        print("There are no query available")
        return []
    query = [user for user in open(path, 'r').read().split("\n")][:-1]
    return query


def LastMediaIndex(path):
    number = 0
    path = path + "\\_last_index.txt"
    if os.path.exists(path):
        number = int(open(path, "r").read())
    return number


def biggest_bitrate_url(medium):
    biggest = 0
    index = 0
    for i in range(len(medium.variants)):
        if medium.variants[i].contentType == "video/mp4":
            bitrate = medium.variants[i].bitrate
            if bitrate > biggest:
                biggest = bitrate
                index = i
    return medium.variants[index].url


def searchContext(p_text="", p_username="", p_since="", p_until=""):
    """
    dates must be in YearMonthDay format (20060321)
    for now we just use the username parameter. The code is not compatible with other parameters
    """
    context = ""
    if p_text != "":
        context += p_text
    if p_username != "":
        context += "(from:" + p_username + ")"
    if p_since != "":
        context += p_since
    if p_until != "":
        context += p_until
    return context


def getMedia(url_list, username):
    path = os.getcwd() + f"\\scraped_data\\{username}"

    last_media = 0
    unfinished = []
    last = LastMediaIndex(path)

    for index in range(len(url_list)):

        if index % 10 == 0 and index != 0: print(f"{index} media scraped", end="\r")

        extension = url_list[index][0]
        response = requests.get(url_list[index][1])
        number = url_list[index][2]
        order = url_list[index][3]

        if index == len(url_list) - 1:
            last_media = number

        try:
            with open(path + f"\\{username}_{last + number}({order}){extension}", 'wb') as fp:
                fp.write(response.content)

        except Exception as ex:
            print(f"An exception occurred during getting media. Exception: {ex}")
            unfinished.append(url_list[index][1])

    open(path + "\\_last_index.txt", "w").write(str(last + last_media))

    if len(unfinished) != 0:
        path = os.getcwd() + f"\\scraped_data\\{username}\\unfinished_media.txt"
        writer = open(path, "a")
        for media in unfinished:
            writer.write(media + "\n")
        print(f"There are {len(unfinished)} media unfinished. Try again later")
        writer.close()
    return


def getTweets(query, date):
    """
    :param date: date of the last tweet we get from the user
    :param query: query is the text we're going to search on Twitter
    :return: Returns two lists. First one is the list of tweets and second one is list of media urls
    """
    num_media = 0
    tweets = []
    media_url_list = []
    for tweet in sntwitter.TwitterSearchScraper(query).get_items():

        index = len(tweets)
        if index % 100 == 0 and index != 0:
            print(f"{index} tweet scraped", end="\r")

        if str(tweet.date.date()) == date[0] and str(tweet.date.time()) == date[1]:
            break

        tweets.append([tweet.content, tweet.date])

        if not tweet.media:
            continue
        num_media += 1
        order = 0
        for medium in tweet.media:
            order += 1
            if isinstance(medium, sntwitter.Photo):
                media_url_list.append([".jpg", medium.fullUrl, num_media, str(order)])
            elif isinstance(medium, sntwitter.Video):
                media_url_list.append([".mp4", biggest_bitrate_url(medium), num_media, str(order)])
            elif isinstance(medium, sntwitter.Gif):
                media_url_list.append([".mp4", medium.variants[0].url, num_media, str(order)])
    return tweets, media_url_list


# ****************************************************************************************************** Main Operations


def update():
    user_list = getUserList()
    for username in user_list:
        scrapQuery(username)
    return


def addQuery():
    path = os.getcwd() + f"\\scraped_data\\query_list.txt"
    query = getUserList()
    if len(query) != 0:
        print(f"Current queries in the list:", query)
    username = input("Write the username you wanted to add to query list: ")
    if username != "q":
        open(path, "a").write(username + "\n")
        print(f"{username} added to query list")
    else:
        print("Operation cancelled")
    time.sleep(2)
    return


def removeQuery():
    path = os.getcwd() + f"\\scraped_data\\query_list.txt"
    query = getUserList()
    if len(query) != 0:
        print(f"Current queries in the list:", query)
        answer = input("Write the username you wanted to remove from query list: ")

        if answer != "q":
            query.remove(answer)
            writer = open(path, "w")
            for user in query:
                writer.write(user + "\n")
            print(f"{answer} removed from query list")
        else:
            print("Operation cancelled")
    else:
        print("There are no query available")
    time.sleep(2)
    return


def continueUnfinished():
    print("continue unfinished yet not created")
    pass


def cancelUnfinished():
    print("cancel unfinished yet not created")
    pass


def scrapQuery(username=""):
    checkQueryDictionary(username)
    date_path = os.getcwd() + f"\\scraped_data\\{username}\\_last_update.txt"

    date = ["2000-01-30", "00:00:00"]
    if os.path.exists(date_path):
        date = open(date_path, "r").read().split(" ")

    print(f"Starting to scrape {username}")
    tweets, media_urls = getTweets(searchContext(p_username=username), date)

    if len(tweets) != 0:
        open(date_path, "w").write(str(tweets[0][1])[:19])

    archive_path = os.getcwd() + f"\\scraped_data\\{username}\\_tweets.feather"

    df = pd.DataFrame(tweets, columns=['Tweet', 'Date'])
    if os.path.exists(archive_path):
        df = df.append(pd.read_csv(archive_path))

    df.to_csv(archive_path)
    print(f"{len(tweets)} tweets scraped successfully")

    getMedia(media_urls, username)
    print(f"{len(media_urls)} media scraped successfully")

    for i in range(10):
        print("*" * i, end="\r")
        time.sleep(0.3)
    print("*******")
    return


# ****************************************************************************************** User Interface (kind of :p)


def currentOperation():
    os.system('cls')
    question = """
    Press 1 to update current queries
    Press 2 to add a new query
    Press 3 to remove a query
    Press 4 to continue unfinished operations
    Press 5 to cancel unfinished operations
    Press 6 to perform one time scraping operation
    Press 7 to see current queries
    Press any other key to terminate session
    Select an operation: 
    """
    answer = input(question)
    os.system('cls')
    start = time.time()
    if answer == "1":
        update()
        print(f"Operation time: {time.time() - start}")
        # return True
    elif answer == "2":
        addQuery()
    elif answer == "3":
        removeQuery()
    elif answer == "4":
        continueUnfinished()
        print(f"Operation time: {time.time() - start}")
        return True
    elif answer == "5":
        cancelUnfinished()
    elif answer == "6":
        scrapQuery(input("Username: "))
    elif answer == "7":
        print(getUserList())
        time.sleep(1)
    else:
        print("Invalid operation\nSession terminated")
        return True


# ***************************************************************************************************************** Main


def main():
    checkScrapDictionary()
    while True:
        if currentOperation():
            break
        time.sleep(2)


if __name__ == '__main__':
    main()
