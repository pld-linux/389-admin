%define prerel .a1

#%global selinux_variants mls targeted

Summary:          389 Administration Server (admin)
Name:             389-admin
Version:          1.1.11
Release:          1%{prerel}
License:          GPLv2 and ASL 2.0
URL:              http://directory.fedoraproject.org/
Group:            System Environment/Daemons
BuildRoot:        %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:    nspr-devel
BuildRequires:    nss-devel
BuildRequires:    svrcore-devel
BuildRequires:    mozldap-devel
BuildRequires:    cyrus-sasl-devel
BuildRequires:    icu
BuildRequires:    libicu-devel >= 4.2.1
BuildRequires:    apache-devel
BuildRequires:    apr-devel
BuildRequires:    apr-util-devel
BuildRequires:    389-adminutil-devel

%if 0
# The following are needed to build the SELinux policy
BuildRequires:    checkpolicy
BuildRequires:    selinux-policy-devel
BuildRequires:    /usr/share/selinux/devel/Makefile
BuildRequires:    389-ds-base-selinux-devel
%endif

Requires:         389-ds-base
Requires:         apache-mod_nss
# the following are needed for some of our scripts
Requires:         perl-Mozilla-LDAP
Requires:         nss-tools

# for the init script
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service

Source0:          http://directory.fedoraproject.org/sources/%{name}-%{version}%{prerel}.tar.bz2
# Source0-md5:	2d5c5e2058429086bbced744590aba7f
#Patch1:           f11-httpd.patch

%description
389 Administration Server is an HTTP agent that provides management features
for 389 Directory Server.  It provides some management web apps that can
be used through a web browser.  It provides the authentication, access control,
and CGI utilities used by the console.

%if 0
%package          selinux
Summary:          SELinux policy for 389 Administration Server
Group:            System Environment/Daemons
Requires:         selinux-policy
Requires:         %{name} = %{version}-%{release}
Requires:         389-ds-base-selinux

%description      selinux
SELinux policy for the 389 Adminstration Server package.
%endif

%prep
%setup -q -n %{name}-%{version}%{prerel}
#%patch1

%build
%{__aclocal} -I m4
%{__automake}
%{__autoconf}
%configure CFLAGS="%rpmcflags `apu-1-config --includes`" \
	--disable-rpath \
	#--with-selinux

%ifarch x86_64 ppc64 ia64 s390x sparc64
export USE_64=1
%endif

%{make}

%if 0
# Build the SELinux policy module for each variant
cd selinux-built
cp %{_datadir}/dirsrv-selinux/dirsrv.if .
cp %{_datadir}/dirsrv-selinux/dirsrv.te .
for selinuxvariant in %{selinux_variants}
do
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
  mv dirsrv-admin.pp dirsrv-admin.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -
%endif

%install
rm -rf $RPM_BUILD_ROOT 

make DESTDIR="$RPM_BUILD_ROOT" install

# make console jars directory
mkdir -p $RPM_BUILD_ROOT%{_datadir}/dirsrv/html/java

#remove libtool and static libs
rm -f $RPM_BUILD_ROOT%{_libdir}/*.a
rm -f $RPM_BUILD_ROOT%{_libdir}/*.so
rm -f $RPM_BUILD_ROOT%{_libdir}/*.la
rm -f $RPM_BUILD_ROOT%{_libdir}/dirsrv/modules/*.a
rm -f $RPM_BUILD_ROOT%{_libdir}/dirsrv/modules/*.la

%if 0
# Install the SELinux policy
cd selinux-built
for selinuxvariant in %{selinux_variants}
do
  install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
  install -p -m 644 dirsrv-admin.pp.${selinuxvariant} \
    %{buildroot}%{_datadir}/selinux/${selinuxvariant}/dirsrv-admin.pp
done
cd -
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/chkconfig --add dirsrv-admin
/sbin/ldconfig

%preun
if [ $1 = 0 ]; then
        /sbin/service dirsrv-admin stop >/dev/null 2>&1 || :
        /sbin/chkconfig --del dirsrv-admin
fi

%postun -p /sbin/ldconfig

%if 0
%post selinux
if [ "$1" -le "1" ] ; then # First install
for selinuxvariant in %{selinux_variants}
do
  semodule -s ${selinuxvariant} -i %{_datadir}/selinux/${selinuxvariant}/dirsrv-admin.pp 2>/dev/null || :
done
fixfiles -R %{name} restore || :
/sbin/service dirsrv-admin condrestart > /dev/null 2>&1 || :
fi

%preun selinux
if [ "$1" -lt "1" ]; then # Final removal
for selinuxvariant in %{selinux_variants}
do
  semodule -s ${selinuxvariant} -r dirsrv-admin 2>/dev/null || :
done
fixfiles -R %{name} restore || :
/sbin/service dirsrv-admin condrestart > /dev/null 2>&1 || :
fi

%postun selinux
if [ "$1" -ge "1" ]; then # Upgrade
for selinuxvariant in %{selinux_variants}
do
  semodule -s ${selinuxvariant} -i %{_datadir}/selinux/${selinuxvariant}/dirsrv-admin.pp 2>/dev/null || :
done
fi
%endif

%files
%defattr(-,root,root,-)
%doc LICENSE
%dir %{_sysconfdir}/dirsrv/admin-serv
%config(noreplace)%{_sysconfdir}/dirsrv/admin-serv/*.conf
%{_datadir}/dirsrv
%{_sysconfdir}/rc.d/init.d/dirsrv-admin
%config(noreplace)%{_sysconfdir}/sysconfig/dirsrv-admin
%{_sbindir}/*
%{_libdir}/*.so.*
%{_libdir}/dirsrv
%{_mandir}/man8/*

%if 0
%files selinux
%defattr(-,root,root,-)
%{_datadir}/selinux/*/dirsrv-admin.pp
%endif

%changelog
