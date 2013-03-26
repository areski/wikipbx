#!/bin/sh
#    25.11.2009
#    Description:
#    Developer Faisal Alazemi <faisal.alazemi@aldimna.com>

#    Install-WikiPBX-Ubuntu-9.10-Server.sh - install WikiPBX, FreeSWITCH and all packages requisites.
#    Copyright (C) 2009 AlDimna Softwaer, Inc. 
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Install-WikiPBX-Ubuntu-9.10-Server.sh  Copyright (C) 2009 AlDimna Softwaer, Inc. 
#    This program comes with ABSOLUTELY NO WARRANTY.
#    This is free software, and you are welcome to redistribute it
#    under certain conditions.

sleep .5
BasePath="$0"
Date=$(date +%d-%m-%Y-%T)
case $BasePath in
    (Install-WikiPBX-Ubuntu-9.10-Server.sh)
        BasePath=""
    ;;
    (*)
        BasePath=${BasePath%Install-WikiPBX-Ubuntu-9.10-Server.sh*}
    ;;
esac   

Version="1.0.0.0" #Pre-Alpha
Version="1.0.0.1" #Alpha
Version="1.0.1.1" #beta
Version="1.0.1.2" #beta
Version="1.0.1.3" #beta
#Version="1.0.2.1" #release candidate
#Version="1.0.3.1" #public release

ScriptDescription="This sicript will install WikiPBX, FreeSWITCH and all packages requisites. \
                        \n\tpackages requisites: \
                            \n\t\tbuild-essential subversion subversion-tools \
                            \n\t\tautomake1.9 gcc-4.1 autoconf make wget \
                            \n\t\tlibtool g++ libncurses5 libncurses5-dev \
                            \n\t\tlibgdbm-dev  libperl-dev python2.5 python2.5-dev \
                            \n\t\tlibgnutls-dev libtiff4-dev  libx11-dev mysql-server python-mysqldb \
                        \n\tVersion: $Version" 
ContentString="Content String."
FooterCase="press" # wait|press|exit

HTMLLog="/usr/src/WikiPBX-freeswitch-log($Date).htm"
TextLog="/usr/src/WikiPBX-freeswitch-log($Date)"

Title(){
	echo -n "\033]0;Install-WikiPBX-Ubuntu-9.10-Server - $@\007"
}
Header(){
        clear
        ContentString="$Date"
	
        echo "\033[1;7mAlDimna Softwaer, Inc.\033[0m"
        echo "\n"
        echo -n "\033[1;37m"

        printf "%s%$(($(stty size | cut -d' ' -f2)-${#ContentString}))s" "$ContentString" " [www.aldimna.com] "
        echo "\n" 

        echo "\t$@"

        echo "\033[0m"
}
Content(){
        echo -n "\n\033[1;32m\033[1m"
	ContentString=" * "$@ 
	printf "%s%$(($(stty size | cut -d' ' -f2)-${#ContentString}))s" "$ContentString" " [ OK ] "
        echo "\033[0m\n"
}
Skip(){
    ContentString=" * "$@ 
    echo -n "\033[1;31m"
    printf "%s%$(($(stty size | cut -d' ' -f2)-${#ContentString}))s" "$ContentString" " [ Skipped ] "
    echo "\033[0m"
}
PayAttention(){
	    echo -n "\033[1;7m"
            echo -n "$@"
            echo   "\033[0m"
}

Question(){
    echo -n "$@ - Do you want to continue [Y/n]?"
}
Error(){
    Err="$(tail -1 $HTMLLog)" #ReadLastLine
    case "$Err" in
        ("</pre></dd>")
            Err="$(tail -1 $HTMLLog)" 
        ;;
        ("+-----------------------------------------------+")
            Err="$(tail -1 $HTMLLog)" 
        ;;
        ("Checked out revision 227.")
            Err="$(tail -1 $HTMLLog)"
        ;;
 	(*)
            ContentString=" * $Err"
            echo -n "\033[1;31m"
            printf "%s%$(($(stty size | cut -d' ' -f2)-${#ContentString}))s" "$ContentString" " [ Error ] "
            echo "\033[0m"
       	;;
    esac   
   
}
 
Footer(){
	echo "\n\033[1;32m\033[1mProcess Was Completed Successfully..."
	case "$1" in
            (Wait|wait)
		echo "Will continue in 5 Sconds...\033[0m\n"
    		sleep 5 
            ;;
            (Press|press)
                echo -n "\033]0;"
                echo "\007"
                echo "\t\tTo start Freeswitch cd /usr/local/freeswitch/bin"
                echo "\t\tcd /usr/local/freeswitch/bin"
                echo "\t\tsudo ./freeswitch"
                echo "\t\tTehn Navigate to wikipbx.yourserver.net"
                
                echo "\007"
                #open wikipbx.aldimna.com
            
                echo "Press any Key to Exit...\033[0m\n"
                read x
                
            ;;
            (UPress|upress)
                echo "Press any Key to Exit...\033[0m\n"
                read x
            ;;

            (*)
                echo "Exit...\033[0m\n"
    		exit 0
            ;;
	esac
	tput sgr0
}

Progressing(){
    case $1 in
        (Start|start)
            ProgressingStart
        ;;
        (Finished|finished)
            ProgressingFinished $2 
    	;;
  	(*)
          Skip  Progressing
    	;;
    esac
    
}

ProgressingStart(){
    percentage="|"
    other_data="Progressing: Please wait..."
    while true
        do
            echo -n "\t${other_data}[${percentage}] \r"
            sleep .5
            case $percentage in
                ("|")
                    percentage="/"
                ;;
                ("/")
                    percentage="-"
                ;;
                ("-")
                    percentage="\\"
                ;;
                ("\\")
                    percentage="|"
                ;;
                (*)
                    percentage="*"
                ;;
            esac
   done
}

ProgressingFinished(){
    PID=$1
    kill $PID #>/dev/null 2>&1
    echo -n "\t\t\t\t...\033[1;32m\033[1m[done]\033[0m"
    echo
}
Download(){
    if [ ! -f $1 ] ; then
        wget $2
       Content "Download [$1]"
    else
        Content "[$1] is allready has been Downloaded"    
    fi
}

HTML(){
    case $1 in
        (Head)
            echo "<!-- " > $HTMLLog
            chmod 666 $HTMLLog
            echo "        Index.html " >> $HTMLLog  
            echo "        01.10.2009 " >> $HTMLLog
            echo "        Copyright 2009 AlDimna Softwaer, Inc. " >> $HTMLLog
            echo "        Developer Faisal Alazemi <faisal.alazemi@aldimna.com> " >> $HTMLLog
            echo "        Description: install WikiPBX, FreeSWITCH and all packages requisites" >> $HTMLLog
            echo "--> " >> $HTMLLog
            echo '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">' >> $HTMLLog
            echo '<html xmlns="http://www.w3.org/1999/xhtml" >' >> $HTMLLog
            echo '<head>' >> $HTMLLog
            echo '<title>AlDimna Softwaer, Inc. - install WikiPBX, FreeSWITCH and all packages requisites</title>' >> $HTMLLog
            echo '<meta http-equiv="content-type" content="application/xhtml+xml;charset=utf-8"/>' >> $HTMLLog
            echo '<meta http-equiv="Content-Style-Type" content="text/css"/>' >> $HTMLLog
            echo '<meta http-equiv="Content-Script-Type" content="text/javascript"/>' >> $HTMLLog
            echo '<meta name="generator" content="AlDimna Softwaer, Inc."/>' >> $HTMLLog
            echo '<meta name="Author" content="Faisal Alazemi"/>' >> $HTMLLog
            echo '<meta name="copyright" content="&copy; 2000 AlDimna Software, Inc."/>' >> $HTMLLog
            echo '<meta name="description" content="install WikiPBX, FreeSWITCH and all packages requisites"/>' >> $HTMLLog
            echo '<meta name="keywords" content="install WikiPBX, FreeSWITCH and all packages requisites"/>' >> $HTMLLog
            echo '<link rel="shortcut icon" href="http://ws.aldimna.com/images/Logos/Default/Icons/logo.ico" />' >> $HTMLLog
            echo '<link  href="http://ws.aldimna.com/App_Themes/Default/StyleSheet.css" type="text/css" rel="Stylesheet" />' >> $HTMLLog
            echo '<style type="text/css">.Content { } .Content  { padding: 10px 20px; } .Content  > h3 { padding: 0; margin:0; } .Content  > dl {     padding: 0; margin: 0;}</style>' >> $HTMLLog
            echo '</head>' >> $HTMLLog
            echo "<body><div id='Container'>" >> $HTMLLog
            echo "<div id='Header'>" >> $HTMLLog
            echo "<div>" >> $HTMLLog
            echo "<h1 id='Header_Title'>" >> $HTMLLog
            echo "<a href='WikiPBX-freeswitch-log.htm' title='AlDimna Tutorials'>AlDimna Logs</a></h1>" >> $HTMLLog
            echo "<h2 id='Header_Qout'></h2>" >> $HTMLLog
            echo "</div>" >> $HTMLLog
            
            echo '<div class="AccountMsg">' >> $HTMLLog
            echo '<h3>Summary</h3>' >> $HTMLLog
            echo '<p>' >> $HTMLLog
            echo 'This sicript will install WikiPBX, FreeSWITCH and all packages requisites.</p>' >> $HTMLLog
            echo '<p>Version: '$Version' </p>' >> $HTMLLog
            echo '</div>' >> $HTMLLog
            
            echo "</div>" >> $HTMLLog
            
            
        ;;
 
        (Footer)
            echo '</dl></div>' >> $HTMLLog
            echo '<div id="Footer">' >> $HTMLLog
                echo '<dl>' >> $HTMLLog
                echo '<dt><a href="#" title="References">References</a></dt>' >> $HTMLLog
                echo '<dd>' >> $HTMLLog
                echo '<p>' >> $HTMLLog
                echo '<a href="http://wikipbx.subwiki.com/installation-manual-0-8"' >> $HTMLLog
                echo 'title="wikipbx.subwiki.com installation manual 0.8">wikipbx.subwiki.com installation manual 0.8</a>' >> $HTMLLog
                echo '</p>' >> $HTMLLog
                echo '</dd>' >> $HTMLLog
                echo '</dl>' >> $HTMLLog
            echo '</div>' >> $HTMLLog
            echo "</div></body></html>" >> $HTMLLog
        ;;
 	(*)
           Skip  HTML
    	;;
    esac   
    
    
}
DT(){
    echo "<dt>$1</dt>" >> $HTMLLog 
}
DD(){
    case $1 in
        (Start)
             echo "<dd><pre>" >> $HTMLLog 
        ;;
 	(End)
            echo "</pre></dd>" >> $HTMLLog 
    	;;
    esac     
}


 
Initial(){
 
    Title "Initial"
    Header "$ScriptDescription"
     
    HTML Head
    echo "<div  class='Content'><dl>" >> $HTMLLog
    Title "Prerequisites"
    echo -n "Press I to install U to uninstall?"
    read x
    case $x in
        (i|I)
            Prerequisites
            WikiPBXDependencies
            FreeSWITCH
            WikiPBX
            SettingsTemplate
            Django
            mod_wsgi
            PrepareDatabase
            #InitializeDatabase
            EnableModulesCompileTime
            Rebuild
            EnableModulesRunTime
            Configuremod_xml_curl
            BuildESL
            InitializeDatabase
            ConfigureWikipbxModWsgi
        ;;
        (u|U)
            UnInstall
            FooterCase="UPress"
        ;;
        (*)
            Skip Prerequisites
            FooterCase="UPress"
        ;;
    esac     
    HTML Footer
    Footer "$FooterCase"
}

Prerequisites(){
    Title "Prerequisites"
    Question "Install Prerequisites"
     
    read x
     case $x in
        (yes|Yes|Y|y)
            sudo apt-get -y install build-essential subversion subversion-tools \
                                        automake1.9 gcc-4.1 autoconf make wget \
                                        libtool g++ libncurses5 libncurses5-dev \
                                        libgdbm-dev  libperl-dev \
                                        python2.5 python2.6-dev \
                                        libgnutls-dev libtiff4-dev  libx11-dev \
                                        apache2-threaded-dev \
                                        libapache2-mod-wsgi\
                                        python2.6-dev \
                                        mysql-server python-mysqldb python-tz #>> $HTMLLog > $TextLog
             Content  "Prerequisites"
        ;;
 	(*)
            Skip Prerequisites
    	;;
    esac     
}

WikiPBXDependencies(){
    Question "Install WikiPBX Dependencies"
    read x
     
    case $x in
        (yes|Yes|y|Y)
            cd /usr/src
            Download PyXML-0.8.4.tar.gz http://ufpr.dl.sourceforge.net/sourceforge/pyxml/PyXML-0.8.4.tar.gz
            
            Progressing Start &
            PID=$! 
                DT "Python-Xml"
                DD Start
                    Error "$( sudo tar xvfz PyXML-0.8.4.tar.gz   >> $HTMLLog   2>&1  || > /dev/null   )" 
                    cd PyXML-0.8.4 
                    Error "$( sudo python setup.py build    >> $HTMLLog   2>&1  || > /dev/null   )" 
                    Error "$( sudo python setup.py install   >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End
            Progressing Finished $PID         
            Content "Python-Xml"

            cd /usr/src
            Download log4py-1.3.tar.gz http://ufpr.dl.sourceforge.net/sourceforge/log4py/log4py-1.3.tar.gz
            Progressing Start & 
            PID=$! 
                DT "log4py"
                DD Start
                    Error "$( sudo tar xvfz log4py-1.3.tar.gz    >> $HTMLLog   2>&1  || > /dev/null   )" 
                    cd log4py-1.3
                    Error "$( sudo python setup.py build   >> $HTMLLog   2>&1  || > /dev/null   )" 
                    Error "$(  sudo python setup.py install  >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End
            Progressing Finished $PID         
            Content "log4py"            
        ;;
 	(*)
           Skip WikiPBX Dependencies
     
    	;;
    esac
 
}
FreeSWITCH(){
    Question "Install FreeSWITCH 1.0.4"
    read x
     case $x in
        (yes|Yes|Y|y)
             
            cd /usr/src
            Download  freeswitch-1.0.4.tar.gz http://files.freeswitch.org/freeswitch-1.0.4.tar.gz
            UnZip
             
            Configure
            Make
            MakeInstall
        ;;
 	(*)
              Skip FreeSWITCH
    	;;
    esac
}
UnZip(){
    Question "Unpagck freeswitch-1.0.4.tar.gz"
    read x
    case $x in
        (yes|Yes|Y|y)
            cd /usr/src
            Progressing Start & 
            PID=$!
                DT "UnZip"
                DD Start
                   Error "$( sudo tar xvfz freeswitch-1.0.4.tar.gz    >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End
            Progressing Finished $PID
            cd  freeswitch-1.0.4
            Content "tar xopf freeswitch-1.0.4.tar.gz"
        ;;
 	(*)
                Skip UnZip
    	;;
    esac     

}

Configure(){
    Question "Configure freeswitch-1.0.4 (this may take some time)"
    read x
     case $x in
        (yes|Yes|Y|y)
            Progressing Start & 
            PID=$! 
                cd /usr/src/freeswitch-1.0.4
                DT "Configure"
                DD Start      
                   Error "$( sudo ./configure    >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End      
                Progressing  Finished $PID
            Content "configure"
        ;;
 	(*)
                 Skip Configure
    	;;
    esac     
}

Make(){
     Question "Make freeswitch-1.0.4"
    read x
     case $x in
        (yes|Yes|Y|y)
            Progressing Start & 
            PID=$! 
                cd /usr/src/freeswitch-1.0.4
                DT "Make"
                DD Start
                   Error "$( sudo make   >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End
            Progressing Finished $PID
            Content "make"
        ;;
 	(*)
             Skip Make freeswitch-1.0.4
    	;;
    esac     

}

MakeInstall(){
    Question "Make install freeswitch-1.0.4"
    read x
    case $x in
        (yes|Yes|Y|y)
            Progressing Start & 
            PID=$! 
                cd /usr/src/freeswitch-1.0.4
                DT "make"
                DD Start
                   Error "$( sudo make install  >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End
                Progressing Finished $PID
            Content "make install"
        ;;
 	(*)
            Skip Make install freeswitch-1.0.4
            	
    	;;
    esac     

}

WikiPBX(){
    Question "Install WikiPBX"
    read x
    case $x in
        (yes|Yes|Y|y)
            cd /usr/src
            Progressing Start & 
            PID=$!
                DT "svn wikipbx"
                DD Start       
                  Error "$(  sudo svn co http://svn.wikipbx.org/svn/wikipbx/branches/releases/0.8.0 wikipbx    >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End    
            Progressing Finished $PID
            Content "svn wikipbx"
        ;;
 	(*)
            Skip WikiPBX
            	
    	;;
    esac     
}

SettingsTemplate(){
    Question "Settings Template"
    read x
    case $x in
        (yes|Yes|y|Y)
            Progressing Start & 
            PID=$! #this to catch Progressing PID
                DT "Settings Template"
                DD Start
        
                    cd /usr/src/wikipbx/wikipbx
                    Error "$( sudo cp settings_template.py settings.py    >> $HTMLLog   2>&1  || > /dev/null   )" 
                    Content "cp settings.py"
                    
                    Error "$( sudo mkdir -p /var/log/wikipbx/cdr/err   >> $HTMLLog   2>&1  || > /dev/null   )" 
                    Content "mkdir /var/log/wikipbx/cdr/err"
        
                    Error "$(sed -i "s/DATABASE_ENGINE = 'postgresql'/DATABASE_ENGINE = 'mysql'/g" /usr/src/wikipbx/wikipbx/settings.py    >> $HTMLLog   2>&1  || > /dev/null   )" 
                    Content "DATABASE_ENGINE"
                    
                    Error "$(sed -i "s/DATABASE_USER = 'YOUR_DB_USER'/DATABASE_USER = 'wikipbxuser'/g" /usr/src/wikipbx/wikipbx/settings.py   >> $HTMLLog   2>&1  || > /dev/null   )" 
                    Content "DATABASE_USER"
                    
                    PayAttention  "\n\tChose Password for wikipbxuser?"
                    echo -n "wikipbxuser Passowrd:"
                    read wikipbxuserPassword
                    Error "$(sed -i "s/DATABASE_PASSWORD = 'YOUR_DB_PASS'/DATABASE_PASSWORD = '$wikipbxuserPassword'/g" /usr/src/wikipbx/wikipbx/settings.py   >> $HTMLLog   2>&1  || > /dev/null   )" 
                    Content "DATABASE_PASSWORD"
                    
                    PayAttention  "\n\tChose FREESWITCH_URL_PORT (wikipbx.YourServer.net)?"
                    echo -n "FREESWITCH_URL_PORT:"
                    read FREESWITCH_URL_PORT
                    Error "$(sed -i "s/127.0.0.1/$FREESWITCH_URL_PORT/g" /usr/src/wikipbx/wikipbx/settings.py   >> $HTMLLog   2>&1  || > /dev/null   )" 
                    Content "FREESWITCH_URL_PORT"
                    
                DD End
            Progressing Finished $PID
            Content "create a custom settings.py"
        ;;
        (*)
            Skip Settings Template
        ;;
    esac
}

Django(){
    Question "Install Django"
    read  x
    case $x in
        (yes|Yes|y|Y)
            cd /usr/src
            Progressing Start & 
            PID=$!
                DT "svn django"
                DD Start  
                    Error "$(sudo svn co --revision 5024 http://code.djangoproject.com/svn/django/trunk/ django   >> $HTMLLog   2>&1  || > /dev/null   )" 
            Progressing Finished $PID
            Content "svn Django"
            Error "$(sudo ln -s /usr/src/django/django /usr/lib/python2.6/dist-packages   >> $HTMLLog   2>&1  || > /dev/null   )"
            DD End     
            Content "Symlink in dist-packages"
        ;;
 	(*)
            Skip Django
    	;;
    esac
}

mod_wsgi(){
    Question "Install mod_wsgi"
    read x
    case $x in
        (yes|Yes|y|Y)
            Progressing Start & 
            PID=$!
                DT "mod_wsgi"
                DD Start  
                    echo "LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi.so" >/etc/apache2/mods-available/mod_wsgi.load
                    Content "Edit mod_wsgi.so"
            
                    cd /etc/apache2/mods-enabled
                    Error "$(sudo ln -s ../mods-available/mod_wsgi.load >> $HTMLLog   2>&1  || > /dev/null   )" 
                    Content "Symlink in mods-enabled"
                    Error "$( sudo /etc/init.d/apache2 restart >> $HTMLLog 2>&1  || > /dev/null   )"
                DD End     
            Progressing Finished $PID
            Content "mod_wsgi"  
        ;;
 	(*)
             Skip mod_wsgi
    	;;
    esac

}


PrepareDatabase(){
    Question "Prepare Database"
    read x
    case $x in
        (yes|Yes|y|Y)
        
            PayAttention  "\n\tEnter root Password?"
            echo -n "root Passowrd:"
            read RootPassword
            
            PayAttention  "\n\tChose Password for wikipbxuser?"
            echo -n "wikipbxuser Passowrd:"
            read wikipbxuserPassword
        
        
            PayAttention  "\n\tCreate Database User"
            PayAttention  "\t\tMySQL"
            PayAttention  "\t\t\t type this line when mysql shell start"
            PayAttention  "\tGRANT ALL PRIVILEGES ON wikipbx.* TO wikipbxuser@localhost IDENTIFIED BY '$wikipbxuserPassword';"
            PayAttention  "\t\tPress Enter and then type exit Enter"
            read x
            sudo  mysql mysql --user root -p$RootPassword
            
            mysqladmin -h localhost -u root -p$RootPassword create wikipbx -u wikipbxuser -p$wikipbxuserPassword
            Content "Create Database"
        ;;
 	(*)
            Skip Prepare Database
          
    	;;
    esac
}

InitializeDatabase(){
     Question "Initialize Database"
    read x
    case $x in
        (yes|Yes|y|Y)
            echo "\n\tInitialize Database"
            cd /usr/src/wikipbx/wikipbx
            Progressing Start & 
            PID=$!
                DT "Initialize Database"
                DD Start  
                  Error "$(  sudo python manage.py syncdb     >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End   
            Progressing Finished $PID
            Content "Initialize Database"      
        ;;
 	(*)
            Skip Initialize Database
    	;;
    esac
}


EnableModulesCompileTime(){
    Question "Enable Modules - Compile Time"
    read x
    case $x in
        (yes|Yes|y|Y)
            sed -i "s/#event_handlers\/mod_event_socket/event_handlers\/mod_event_socket/g" /usr/src/freeswitch-1.0.4/modules.conf
            sed -i "s/#xml_int\/mod_xml_curl/xml_int\/mod_xml_curl/g" /usr/src/freeswitch-1.0.4/modules.conf
            sed -i "s/#xml_int\/mod_xml_cdr/xml_int\/mod_xml_cdr/g" /usr/src/freeswitch-1.0.4/modules.conf
        ;;
 	(*)
            Skip Enable Modules - Compile Time
    	;;
    esac
}

Rebuild(){
    Question "Rebuild + Install FreeSWITCH"
    read x
    case $x in
        (yes|Yes|y|Y)
            cd /usr/src/freeswitch-1.0.4
            Progressing Start &
            PID=$!
                DT "Rebuild FreeSWITCH"
                DD Start  
                  Error "$(  sudo make install      >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End   
            Progressing Finished $PID
            Content "Rebuild FreeSWITCH"   
        ;;
 	(*)
            Skip Rebuild
    	;;
    esac

}


 
EnableModulesRunTime(){
    Question "Enable Modules - Run Time"
    read x
    case $x in
        (yes|Yes|y|Y)
            sed -i 's/<!-- <load module="mod_event_socket"\/> -->/<load module="mod_event_socket"\/>/g' /usr/local/freeswitch/conf/autoload_configs/modules.conf.xml
            sed -i 's/<!-- <load module="mod_xml_curl"\/> -->/<load module="mod_xml_curl"\/>/g' /usr/local/freeswitch/conf/autoload_configs/modules.conf.xml
            sed -i 's/<!-- <load module="mod_xml_cdr"\/> -->/<load module="mod_xml_cdr"\/>/g' /usr/local/freeswitch/conf/autoload_configs/modules.conf.xml
        ;;
 	(*)
            Skip Enable Modules - Run Time
    	;;
    esac

}
Configuremod_xml_curl(){
    Question "Configure mod_xml_curl"
    read x
    case $x in
        (yes|Yes|y|Y)
            PayAttention  "\n\tChose gateway-url (wikipbx.YourServer.net)?"
            echo -n "gateway-url:"
            read gateway
            sed -i 's/<param.*name="gateway-url".*\/>/ /g' /usr/local/freeswitch/conf/autoload_configs/xml_curl.conf.xml
            sed -i 's/<binding name="example">/<binding name="example">\n<param name="gateway-url" value="http:\/\/'$gateway'\/xml_dialplan\/" bindings="configuration,dialplan,directory"\/>/g' /usr/local/freeswitch/conf/autoload_configs/xml_curl.conf.xml
        ;;
 	(*)
             Skip Configure mod_xml_curl
    	;;
    esac

}

BuildESL(){
     Question "Build ESL"
    read x
    case $x in
        (yes|Yes|y|Y)
            PayAttention  "\n\tEnter python version(2.6)?"
            echo -n "python version:"
            read var
            sed -i 's/LOCAL_CFLAGS=-I\/usr\/include\/python[0-9].[0-9]/LOCAL_CFLAGS=-I\/usr\/include\/python'$var'/g' /usr/src/freeswitch-1.0.4/libs/esl/python/Makefile
            sed -i 's/LOCAL_LDFLAGS=-lpython[0-9].[0-9]/LOCAL_LDFLAGS=-lpython'$var'/g' /usr/src/freeswitch-1.0.4/libs/esl/python/Makefile
            
            Progressing Start & 
            PID=$!
                DT "Build ESL"
                DD Start
                    cd /usr/src/freeswitch-1.0.4/libs/esl/
                   Error "$( sudo make pymod     >> $HTMLLog   2>&1  || > /dev/null   )" 
                 Error "$(   sudo cp /usr/src/freeswitch-1.0.4/libs/esl/python/_ESL.so /usr/lib/python2.6/dist-packages   >> $HTMLLog   2>&1  || > /dev/null   )" 
                  Error "$(  sudo cp /usr/src/freeswitch-1.0.4/libs/esl/python/ESL.py  /usr/lib/python2.6/dist-packages     >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End 
            Progressing Finished $PID
            Content "Build ESL"   
            ;;
 	(*)
            Skip  Build ESL
    	;;
    esac

}


ConfigureWikipbxModWsgi(){

    Question "Configure Wikipbx Mod Wsgi"
    read x
    case $x in
        (yes|Yes|y|Y)
            
            PayAttention  "\n\tChose ServerName (wikipbx.YourServer.net)?"
            echo -n "ServerName:"
            read ServerName
            
            echo "WSGIPythonPath /usr/src/wikipbx:/usr/src/django:/usr/src/freeswitch/libs/esl/python" > /etc/apache2/sites-available/wikipbx
            echo "" >> /etc/apache2/sites-available/wikipbx
            echo "<VirtualHost *:80>" >> /etc/apache2/sites-available/wikipbx
            echo "ServerAdmin webmaster@$ServerName" >> /etc/apache2/sites-available/wikipbx
            echo "WSGIScriptAlias / /usr/src/wikipbx/wikipbx.wsgi" >> /etc/apache2/sites-available/wikipbx
            echo "ServerName $ServerName" >> /etc/apache2/sites-available/wikipbx
            echo "ErrorLog /var/log/apache2/$ServerName-error.log" >> /etc/apache2/sites-available/wikipbx
            echo "CustomLog /var/log/apache2/$ServerName.log common" >> /etc/apache2/sites-available/wikipbx
            echo "</VirtualHost>" >> /etc/apache2/sites-available/wikipbx
            
            cd /etc/apache2/sites-enabled
                DT "Configure Wikipbx Mod Wsgi"
                DD Start 
                    Error "$( sudo ln -s ../sites-available/wikipbx .    >> $HTMLLog   2>&1  || > /dev/null   )" 
                    Error "$( sudo /etc/init.d/apache2 restart     >> $HTMLLog   2>&1  || > /dev/null   )" 
                    sed -i 's/127.0.0.1.*wikipbx.yourserver.net/ /g' /etc/hosts
                    sed -i 's/127.0.0.1.*'$ServerName'/ /g' /etc/hosts
                    echo "\n127.0.0.1 $ServerName " >> /etc/hosts
                    Error "$( sudo  /etc/init.d/apache2 restart    >> $HTMLLog   2>&1  || > /dev/null   )" 
                DD End
        ;;
 	(*)
            Skip Configure Wikipbx Mod Wsgi
    	;;
    esac
}
 
UnInstall(){
    Question "UnInstall All"
    read x
    case $x in
        (yes|Yes|y|Y)
            cd /usr/src
            echo "" > $TextLog
            Progressing Start & 
            PID=$!
            
                Error "$(sudo rm /usr/src/PyXML-0.8.4.tar.gz >> $HTMLLog    2>&1  || > /dev/null   )" 
                Error "$(sudo rm -r /usr/src/PyXML-0.8.4 >> $HTMLLog    2>&1  || > /dev/null   )"
                Content "UnInstall PyXML-0.8.4"   
                
                Error "$(sudo rm /usr/src/log4py-1.3.tar.gz >> $HTMLLog    2>&1  || > /dev/null   )" 
                Error "$(sudo rm -r /usr/src/log4py-1.3 >> $HTMLLog    2>&1  || > /dev/null   )"
                Content "UnInstall log4py-1.3"   
                
                cd /usr/src/freeswitch-1.0.4
                Error "$(sudo make uninstall >> $HTMLLog     2>&1  || > /dev/null   )"
                Content "UnInstall sudo make uninstall freeswitch-1.0.4"   
                
                Error "$(sudo rm /usr/src/freeswitch-1.0.4.tar.gz >> $HTMLLog    2>&1  || > /dev/null   )" 
                Error "$(sudo rm -r /usr/src/freeswitch-1.0.4 >> $HTMLLog    2>&1  || > /dev/null   )"
                Content "UnInstall freeswitch-1.0.4.tar.gz"   
                
                Error "$(sudo rm -r /usr/local/freeswitch >> $HTMLLog    2>&1  || > /dev/null   )" 
                Content "UnInstall /usr/local/freeswitch"
                
                Error "$(sudo rm -r /usr/src/wikipbx >> $HTMLLog     2>&1  || > /dev/null   )"
                Content "UnInstall wikipbx"
                
                Error "$(sudo rm -r /usr/src/django >> $HTMLLog   2>&1  || > /dev/null   )"
                Content "UnInstall django"
                
                Error "$(sudo rm /usr/lib/python2.6/dist-packages/django >> $HTMLLog    2>&1  || > /dev/null   )"
                Content "UnInstall django Symlink"
                
                Error "$(sudo rm  /etc/apache2/mods-available/mod_wsgi.load >> $HTMLLog   2>&1  || > /dev/null   )" 
                Error "$(sudo rm /etc/apache2/mods-enabled/mod_wsgi.load >> $HTMLLog    2>&1  || > /dev/null   )" 
                Content "UnInstall mod_wsgi.load"
                
                Error "$(sudo rm /usr/lib/python2.6/dist-packages/_ESL.so >> $HTMLLog    2>&1  || > /dev/null   )" 
                Error "$(sudo rm /usr/lib/python2.6/dist-packages/ESL.py >> $HTMLLog    2>&1  || > /dev/null   )"
                Content "UnInstall ESL.py _ESL.so"
                
                
                Error "$(sudo rm /etc/apache2/sites-available/wikipbx >> $HTMLLog   2>&1  || > /dev/null   )" 
                Error "$(sudo rm /etc/apache2/sites-enabled/wikipbx >> $HTMLLog     2>&1  || > /dev/null   )"
                Content "UnInstall wikipbx"

            Progressing Finished $PID
            
            PayAttention  "\n\tEnter root Password?"
            echo -n "root Passowrd:"
            read RootPassword
            mysqladmin -h localhost -u root -p$RootPassword drop wikipbx
            Content "UnInstall drop wikipbx"
            
            Content "UnInstall All"   
        ;;
        (*)
            Skip UnInstall
        ;;
    esac
}



Initial
