# SPDX-FileCopyrightText: 2023 Julian Schauder <pytraeger@schauder.info>
#
# SPDX-License-Identifier: MIT

FROM python:3

RUN pip install pytraeger 

CMD ["python","demo/example02.py"]
