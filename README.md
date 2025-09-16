# write-book
*Write a book using Autonomous Agents*

## Setup

This is assuming you have Python installed on your computer and you are using an IDE such as VS Code or Cursor.

I use Mistral for most of my AI services. If you pull this repo into Cursor, you can ask the built-in AI (vibe code) to change it to use OpenAI or another provdier. 

🏕️ **Setup the virtual envrionment.**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

🛠️ **Install the dependancies**
```bash
pip install mistralai
pip install PyYAML
pip install ebooklib
```

## Commission

There is a file named `commissioning.yaml` where you define everything you want out of the agents. Be detailed but if you define the chapters it will be a little weird otherwise be. as. explcit. as. possible. with. your. expectations.

## Run

In the directory you downloaded it you can run it and call the commissioning file. 

```bash
python make_book.py --commission commissioning.yaml
```

## Outputs

You will find a new directory named "output" that will hold all the files generated for you. 

### Additional Notes

This has taken about 5 miuntes for me to write 16,000 words using the `mistral-tiny` tiny langauge model. 