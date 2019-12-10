FROM ubuntu
RUN apt-get update
RUN apt-get -y dist-upgrade
RUN apt-get install -y build-essential python3-pip python3-dev libssl-dev libcrypto++-dev
RUN apt-get install -y mysql-client libmysqlclient-dev apache2 libapache2-mod-wsgi-py3
COPY install/requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt && rm /tmp/requirements.txt

RUN useradd -m -U -d /home/first -s /bin/bash first
COPY ./server /home/first
RUN chown first:first /home/first

COPY install/vhost.conf /etc/apache2/sites-available/first.conf
COPY install/google_secret.json /usr/local/etc

RUN /usr/sbin/a2dissite 000-default
RUN /usr/sbin/a2ensite first
RUN /usr/sbin/a2enmod ssl
RUN /usr/sbin/a2enmod rewrite

COPY install/run.sh /usr/local/bin
EXPOSE 80
EXPOSE 443
CMD ["/usr/local/bin/run.sh"]
