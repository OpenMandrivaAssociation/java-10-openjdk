%global _disable_ld_no_undefined 1

# We don't usually need slowdebug builds
%bcond_with slowdebug
# Enable release builds by default on relevant arches.
%bcond_without release

# note: parametrized macros are order-sensitive (unlike not-parametrized) even with normal macros
# also necessary when passing it as parameter to other macros. If not macro, then it is considered a switch
# see the difference between global and define:
# See https://github.com/rpm-software-management/rpm/issues/127 to comments at  "pmatilai commented on Aug 18, 2017"
# (initiated in https://bugzilla.redhat.com/show_bug.cgi?id=1482192)
%global debug_suffix_unquoted -slowdebug
# quoted one for shell operations
%global debug_suffix "%{debug_suffix_unquoted}"
%global normal_suffix ""

# if you want only debug build but providing java build only normal build but set normalbuild_parameter
%global debug_warning This package has full debug on. Install only in need and remove asap.
%global debug_on with full debug on
%global for_debug for packages with debug on

%if %{with release}
%global include_normal_build 1
%else
%global include_normal_build 0
%endif

%if %{include_normal_build}
%global build_loop1 %{normal_suffix}
%else
%global build_loop1 %{nil}
%endif

# we need to distinguish between big and little endian PPC64
%global ppc64le         ppc64le
%global ppc64be         ppc64 ppc64p7
%global multilib_arches %{power64} sparc64 %{x86_64}
%global jit_arches      %{ix86} %{x86_64} sparcv9 sparc64 %{aarch64} %{power64} %{arm} s390x
%global aot_arches      %{x86_64}

# By default, we build a debug build during main build on JIT architectures
%if %{with slowdebug}
%ifarch %{jit_arches}
%ifnarch %{arm}
%global include_debug_build 1
%else
%global include_debug_build 0
%endif
%else
%global include_debug_build 0
%endif
%else
%global include_debug_build 0
%endif

%if %{include_debug_build}
%global build_loop2 %{debug_suffix}
%else
%global build_loop2 %{nil}
%endif

# if you disable both builds, then the build fails
%global build_loop  %{build_loop1} %{build_loop2}
# note: that order: normal_suffix debug_suffix, in case of both enabled
# is expected in one single case at the end of the build
%global rev_build_loop  %{build_loop2} %{build_loop1}

%ifarch %{jit_arches}
%global bootstrap_build 1
%else
%global bootstrap_build 1
%endif

%if %{bootstrap_build}
%global targets bootcycle-images all docs
%else
%global targets all docs
%endif


# Filter out flags from the optflags macro that cause problems with the OpenJDK build
# We filter out -O flags so that the optimization of HotSpot is not lowered from O3 to O2
# We filter out -Wall which will otherwise cause HotSpot to produce hundreds of thousands of warnings (100+mb logs)
# We replace it with -Wformat (required by -Werror=format-security) and -Wno-cpp to avoid FORTIFY_SOURCE warnings
# We filter out -fexceptions as the HotSpot build explicitly does -fno-exceptions and it's otherwise the default for C++
%ifarch %{arm}
# Let's see if reducing the optimization level makes it not crash...
%global ourflags -O1 -fno-strict-aliasing
%else
%global ourflags %(echo %optflags | sed -e 's|-Wall|-Wformat -Wno-cpp|' | sed -r -e 's|-O[0-9sz]*||')
%endif
%global ourcppflags %(echo %ourflags | sed -e 's|-fexceptions||')
%global ourldflags %{ldflags}

# With disabled nss is NSS deactivated, so NSS_LIBDIR can contain the wrong path
# the initialization must be here. Later the pkg-config have buggy behavior
# looks like openjdk RPM specific bug
# Always set this so the nss.cfg file is not broken
%global NSS_LIBDIR %(pkg-config --variable=libdir nss)
%global NSS_LIBS %(pkg-config --libs nss)
%global NSS_CFLAGS %(pkg-config --cflags nss-softokn)
# see https://bugzilla.redhat.com/show_bug.cgi?id=1332456
%global NSSSOFTOKN_BUILDTIME_NUMBER %(pkg-config --modversion nss-softokn || : )
%global NSS_BUILDTIME_NUMBER %(pkg-config --modversion nss || : )
# this is workaround for processing of requires during srpm creation
%global NSSSOFTOKN_BUILDTIME_VERSION %(if [ "x%{NSSSOFTOKN_BUILDTIME_NUMBER}" == "x" ] ; then echo "" ;else echo ">= %{NSSSOFTOKN_BUILDTIME_NUMBER}" ;fi)
%global NSS_BUILDTIME_VERSION %(if [ "x%{NSS_BUILDTIME_NUMBER}" == "x" ] ; then echo "" ;else echo ">= %{NSS_BUILDTIME_NUMBER}" ;fi)


# Fix for https://bugzilla.redhat.com/show_bug.cgi?id=1111349.
# See also https://bugzilla.redhat.com/show_bug.cgi?id=1590796
# as to why some libraries *cannot* be excluded. In particular,
# these are:
# libjsig.so, libjava.so, libjawt.so, libjvm.so and libverify.so
%global _privatelibs libjsoundalsa[.]so.*|libsplashscreen[.]so.*|libawt_xawt[.]so.*|libjli[.]so.*|libattach[.]so.*|libawt[.]so.*|libextnet[.]so.*|libawt_headless[.]so.*|libdt_socket[.]so.*|libfontmanager[.]so.*|libinstrument[.]so.*|libj2gss[.]so.*|libj2pcsc[.]so.*|libj2pkcs11[.]so.*|libjaas_unix[.]so.*|libjavajpeg[.]so.*|libjdwp[.]so.*|libjimage[.]so.*|libjsound[.]so.*|liblcms[.]so.*|libmanagement[.]so.*|libmanagement_agent[.]so.*|libmanagement_ext[.]so.*|libmlib_image[.]so.*|libnet[.]so.*|libnio[.]so.*|libprefs[.]so.*|librmi[.]so.*|libsaproc[.]so.*|libsctp[.]so.*|libsunec[.]so.*|libunpack[.]so.*|libzip[.]so.*|lib[.]so\\(SUNWprivate_.*

%global __provides_exclude ^(%{_privatelibs})$
%global __requires_exclude ^(%{_privatelibs})$

# In some cases, the arch used by the JDK does
# not match _arch.
# Also, in some cases, the machine name used by SystemTap
# does not match that given by _build_cpu
%ifarch %{x86_64}
%global archinstall amd64
%endif
%ifarch ppc
%global archinstall ppc
%endif
%ifarch %{ppc64be}
%global archinstall ppc64
%endif
%ifarch %{ppc64le}
%global archinstall ppc64le
%endif
%ifarch %{ix86}
%global archinstall i686
%endif
%ifarch ia64
%global archinstall ia64
%endif
%ifarch s390
%global archinstall s390
%endif
%ifarch s390x
%global archinstall s390x
%endif
%ifarch %{arm}
%global archinstall arm
%endif
%ifarch %{aarch64}
%global archinstall aarch64
%endif
# 32 bit sparc, optimized for v9
%ifarch sparcv9
%global archinstall sparc
%endif
# 64 bit sparc
%ifarch sparc64
%global archinstall sparcv9
%endif
%ifnarch %{jit_arches}
%global archinstall %{_arch}
%endif



%ifarch %{jit_arches}
%global with_systemtap 1
%else
%global with_systemtap 0
%endif

# New Version-String scheme-style defines
%global majorver 10
%global securityver 2

# Standard JPackage naming and versioning defines
%global origin          openjdk
%global origin_nice     OpenJDK
%global top_level_dir_name   %{origin}
%global minorver        0
%global buildver        13
# priority must be 7 digits in total
# setting to 1, so debug ones can have 0
%global priority        00000%{minorver}1
%global newjavaver      %{majorver}.%{minorver}.%{securityver}

%global javaver         %{majorver}

# parametrized macros are order-sensitive
%global compatiblename  java-%{majorver}-%{origin}
%global fullversion     %{compatiblename}-%{version}-%{release}
# images stub
%global jdkimage       jdk
# output dir stub
%define buildoutputdir() %{expand:openjdk/build%{?1}}
# we can copy the javadoc to not arched dir, or make it not noarch
%define uniquejavadocdir()    %{expand:%{fullversion}%{?1}}
# main id and dir of this jdk
%define uniquesuffix()        %{expand:%{fullversion}.%{_arch}%{?1}}

%global etcjavasubdir     %{_sysconfdir}/java/java-%{javaver}-%{origin}
%define etcjavadir()      %{expand:%{etcjavasubdir}/%{uniquesuffix -- %{?1}}}
# Standard JPackage directories and symbolic links.
%define sdkdir()        %{expand:%{uniquesuffix -- %{?1}}}
%define jrelnk()        %{expand:jre-%{javaver}-%{origin}-%{version}-%{release}.%{_arch}%{?1}}

%define sdkbindir()     %{expand:%{_jvmdir}/%{sdkdir -- %{?1}}/bin}
%define jrebindir()     %{expand:%{_jvmdir}/%{sdkdir -- %{?1}}/bin}

%global rpm_state_dir %{_localstatedir}/lib/rpm-state/

%if %{with_systemtap}
# Where to install systemtap tapset (links)
# We would like these to be in a package specific sub-dir,
# but currently systemtap doesn't support that, so we have to
# use the root tapset dir for now. To distinguish between 64
# and 32 bit architectures we place the tapsets under the arch
# specific dir (note that systemtap will only pickup the tapset
# for the primary arch for now). Systemtap uses the machine name
# aka build_cpu as architecture specific directory name.
%global tapsetroot /usr/share/systemtap
%global tapsetdirttapset %{tapsetroot}/tapset/
%global tapsetdir %{tapsetdirttapset}/%{_build_cpu}
%endif

# not-duplicated scriptlets for normal/debug packages
%global update_desktop_icons /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :


%define post_script() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
exit 0
}


%define post_headless() %{expand:
%ifarch %{jit_arches}
# MetaspaceShared::generate_vtable_methods not implemented for PPC JIT
%ifnarch %{ppc64le}
# see https://bugzilla.redhat.com/show_bug.cgi?id=513605
%{jrebindir -- %{?1}}/java -Xshare:dump >/dev/null 2>/dev/null
%endif
%endif

PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

ext=.gz
alternatives \\
  --install %{_bindir}/java java %{jrebindir -- %{?1}}/java $PRIORITY  --family %{name}.%{_arch} \\
  --slave %{_jvmdir}/jre jre %{_jvmdir}/%{sdkdir -- %{?1}} \\
  --slave %{_bindir}/jjs jjs %{jrebindir -- %{?1}}/jjs \\
  --slave %{_bindir}/keytool keytool %{jrebindir -- %{?1}}/keytool \\
  --slave %{_bindir}/orbd orbd %{jrebindir -- %{?1}}/orbd \\
  --slave %{_bindir}/pack200 pack200 %{jrebindir -- %{?1}}/pack200 \\
  --slave %{_bindir}/rmid rmid %{jrebindir -- %{?1}}/rmid \\
  --slave %{_bindir}/rmiregistry rmiregistry %{jrebindir -- %{?1}}/rmiregistry \\
  --slave %{_bindir}/servertool servertool %{jrebindir -- %{?1}}/servertool \\
  --slave %{_bindir}/tnameserv tnameserv %{jrebindir -- %{?1}}/tnameserv \\
  --slave %{_bindir}/unpack200 unpack200 %{jrebindir -- %{?1}}/unpack200 \\
  --slave %{_mandir}/man1/java.1$ext java.1$ext \\
  %{_mandir}/man1/java-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jjs.1$ext jjs.1$ext \\
  %{_mandir}/man1/jjs-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/keytool.1$ext keytool.1$ext \\
  %{_mandir}/man1/keytool-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/orbd.1$ext orbd.1$ext \\
  %{_mandir}/man1/orbd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/pack200.1$ext pack200.1$ext \\
  %{_mandir}/man1/pack200-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmid.1$ext rmid.1$ext \\
  %{_mandir}/man1/rmid-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmiregistry.1$ext rmiregistry.1$ext \\
  %{_mandir}/man1/rmiregistry-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/servertool.1$ext servertool.1$ext \\
  %{_mandir}/man1/servertool-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/tnameserv.1$ext tnameserv.1$ext \\
  %{_mandir}/man1/tnameserv-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/unpack200.1$ext unpack200.1$ext \\
  %{_mandir}/man1/unpack200-%{uniquesuffix -- %{?1}}.1$ext

for X in %{origin} %{javaver} ; do
  alternatives --install %{_jvmdir}/jre-"$X" jre_"$X" %{_jvmdir}/%{sdkdir -- %{?1}} $PRIORITY --family %{name}.%{_arch}
done

update-alternatives --install %{_jvmdir}/jre-%{javaver}-%{origin} jre_%{javaver}_%{origin} %{_jvmdir}/%{jrelnk -- %{?1}} $PRIORITY  --family %{name}.%{_arch}


update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

# see pretrans where this file is declared
# also see that pretrans is only for non-debug
if [ ! "%{?1}" == %{debug_suffix} ]; then
  if [ -f %{_libexecdir}/copy_jdk_configs_fixFiles.sh ] ; then
    sh  %{_libexecdir}/copy_jdk_configs_fixFiles.sh %{rpm_state_dir}/%{name}.%{_arch}  %{_jvmdir}/%{sdkdir -- %{?1}}
  fi
fi

exit 0
}

%define postun_script() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{update_desktop_icons}
fi
exit 0
}


%define postun_headless() %{expand:
  alternatives --remove java %{jrebindir -- %{?1}}/java
  alternatives --remove jre_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}}
  alternatives --remove jre_%{javaver} %{_jvmdir}/%{sdkdir -- %{?1}}
  alternatives --remove jre_%{javaver}_%{origin} %{_jvmdir}/%{jrelnk -- %{?1}}
}

%define posttrans_script() %{expand:
%{update_desktop_icons}
}

%define post_devel() %{expand:

PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

ext=.gz
alternatives \\
  --install %{_bindir}/javac javac %{sdkbindir -- %{?1}}/javac $PRIORITY  --family %{name}.%{_arch} \\
  --slave %{_jvmdir}/java java_sdk %{_jvmdir}/%{sdkdir -- %{?1}} \\
  --slave %{_bindir}/appletviewer appletviewer %{sdkbindir -- %{?1}}/appletviewer \\
%ifarch %{aot_arches}
  --slave %{_bindir}/jaotc jaotc %{sdkbindir -- %{?1}}/jaotc \\
%endif
  --slave %{_bindir}/jlink jlink %{sdkbindir -- %{?1}}/jlink \\
  --slave %{_bindir}/jmod jmod %{sdkbindir -- %{?1}}/jmod \\
  --slave %{_bindir}/jhsdb jhsdb %{sdkbindir -- %{?1}}/jhsdb \\
  --slave %{_bindir}/idlj idlj %{sdkbindir -- %{?1}}/idlj \\
  --slave %{_bindir}/jar jar %{sdkbindir -- %{?1}}/jar \\
  --slave %{_bindir}/jarsigner jarsigner %{sdkbindir -- %{?1}}/jarsigner \\
  --slave %{_bindir}/javadoc javadoc %{sdkbindir -- %{?1}}/javadoc \\
  --slave %{_bindir}/javap javap %{sdkbindir -- %{?1}}/javap \\
  --slave %{_bindir}/jcmd jcmd %{sdkbindir -- %{?1}}/jcmd \\
  --slave %{_bindir}/jconsole jconsole %{sdkbindir -- %{?1}}/jconsole \\
  --slave %{_bindir}/jdb jdb %{sdkbindir -- %{?1}}/jdb \\
  --slave %{_bindir}/jdeps jdeps %{sdkbindir -- %{?1}}/jdeps \\
  --slave %{_bindir}/jdeprscan jdeprscan %{sdkbindir -- %{?1}}/jdeprscan \\
  --slave %{_bindir}/jimage jimage %{sdkbindir -- %{?1}}/jimage \\
  --slave %{_bindir}/jinfo jinfo %{sdkbindir -- %{?1}}/jinfo \\
  --slave %{_bindir}/jmap jmap %{sdkbindir -- %{?1}}/jmap \\
  --slave %{_bindir}/jps jps %{sdkbindir -- %{?1}}/jps \\
  --slave %{_bindir}/jrunscript jrunscript %{sdkbindir -- %{?1}}/jrunscript \\
  --slave %{_bindir}/jshell jshell %{sdkbindir -- %{?1}}/jshell \\
  --slave %{_bindir}/jstack jstack %{sdkbindir -- %{?1}}/jstack \\
  --slave %{_bindir}/jstat jstat %{sdkbindir -- %{?1}}/jstat \\
  --slave %{_bindir}/jstatd jstatd %{sdkbindir -- %{?1}}/jstatd \\
  --slave %{_bindir}/rmic rmic %{sdkbindir -- %{?1}}/rmic \\
  --slave %{_bindir}/schemagen schemagen %{sdkbindir -- %{?1}}/schemagen \\
  --slave %{_bindir}/serialver serialver %{sdkbindir -- %{?1}}/serialver \\
  --slave %{_bindir}/wsgen wsgen %{sdkbindir -- %{?1}}/wsgen \\
  --slave %{_bindir}/wsimport wsimport %{sdkbindir -- %{?1}}/wsimport \\
  --slave %{_bindir}/xjc xjc %{sdkbindir -- %{?1}}/xjc \\
  --slave %{_mandir}/man1/appletviewer.1$ext appletviewer.1$ext \\
  %{_mandir}/man1/appletviewer-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/idlj.1$ext idlj.1$ext \\
  %{_mandir}/man1/idlj-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jar.1$ext jar.1$ext \\
  %{_mandir}/man1/jar-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jarsigner.1$ext jarsigner.1$ext \\
  %{_mandir}/man1/jarsigner-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javac.1$ext javac.1$ext \\
  %{_mandir}/man1/javac-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javadoc.1$ext javadoc.1$ext \\
  %{_mandir}/man1/javadoc-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javap.1$ext javap.1$ext \\
  %{_mandir}/man1/javap-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jcmd.1$ext jcmd.1$ext \\
  %{_mandir}/man1/jcmd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jconsole.1$ext jconsole.1$ext \\
  %{_mandir}/man1/jconsole-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jdb.1$ext jdb.1$ext \\
  %{_mandir}/man1/jdb-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jdeps.1$ext jdeps.1$ext \\
  %{_mandir}/man1/jdeps-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jinfo.1$ext jinfo.1$ext \\
  %{_mandir}/man1/jinfo-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jmap.1$ext jmap.1$ext \\
  %{_mandir}/man1/jmap-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jps.1$ext jps.1$ext \\
  %{_mandir}/man1/jps-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jrunscript.1$ext jrunscript.1$ext \\
  %{_mandir}/man1/jrunscript-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstack.1$ext jstack.1$ext \\
  %{_mandir}/man1/jstack-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstat.1$ext jstat.1$ext \\
  %{_mandir}/man1/jstat-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstatd.1$ext jstatd.1$ext \\
  %{_mandir}/man1/jstatd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmic.1$ext rmic.1$ext \\
  %{_mandir}/man1/rmic-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/schemagen.1$ext schemagen.1$ext \\
  %{_mandir}/man1/schemagen-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/serialver.1$ext serialver.1$ext \\
  %{_mandir}/man1/serialver-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/wsgen.1$ext wsgen.1$ext \\
  %{_mandir}/man1/wsgen-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/wsimport.1$ext wsimport.1$ext \\
  %{_mandir}/man1/wsimport-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/xjc.1$ext xjc.1$ext \\
  %{_mandir}/man1/xjc-%{uniquesuffix -- %{?1}}.1$ext

for X in %{origin} %{javaver} ; do
  alternatives \\
    --install %{_jvmdir}/java-"$X" java_sdk_"$X" %{_jvmdir}/%{sdkdir -- %{?1}} $PRIORITY  --family %{name}.%{_arch}
done

update-alternatives --install %{_jvmdir}/java-%{javaver}-%{origin} java_sdk_%{javaver}_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}} $PRIORITY  --family %{name}.%{_arch}

update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

exit 0
}

%define postun_devel() %{expand:
  alternatives --remove javac %{sdkbindir -- %{?1}}/javac
  alternatives --remove java_sdk_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}}
  alternatives --remove java_sdk_%{javaver} %{_jvmdir}/%{sdkdir -- %{?1}}
  alternatives --remove java_sdk_%{javaver}_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}}

update-desktop-database %{_datadir}/applications &> /dev/null || :

if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{update_desktop_icons}
fi
exit 0
}

%define posttrans_devel() %{expand:
%{update_desktop_icons}
}

%define post_javadoc() %{expand:

PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

alternatives \\
  --install %{_javadocdir}/java javadocdir %{_javadocdir}/%{uniquejavadocdir -- %{?1}}/api \\
  $PRIORITY  --family %{name}
exit 0
}

%define postun_javadoc() %{expand:
  alternatives --remove javadocdir %{_javadocdir}/%{uniquejavadocdir -- %{?1}}/api
exit 0
}

%define post_javadoc_zip() %{expand:

PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

alternatives \\
  --install %{_javadocdir}/java-zip javadoczip %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip \\
  $PRIORITY  --family %{name}
exit 0
}

%define postun_javadoc_zip() %{expand:
  alternatives --remove javadoczip %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip
exit 0
}

%define files_jre() %{expand:
%{_datadir}/icons/hicolor/*x*/apps/java-%{javaver}-%{origin}.png
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjsoundalsa.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libsplashscreen.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libawt_xawt.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjawt.so
}


%define files_jre_headless() %{expand:
%license %{_jvmdir}/%{sdkdir -- %{?1}}/legal
%dir %{_sysconfdir}/.java/.systemPrefs
%dir %{_sysconfdir}/.java
%dir %{_jvmdir}/%{sdkdir -- %{?1}}
%{_jvmdir}/%{sdkdir -- %{?1}}/release
%{_jvmdir}/%{jrelnk -- %{?1}}
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/bin
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/java
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jjs
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/keytool
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/orbd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/pack200
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmid
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmiregistry
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/servertool
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/tnameserv
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/unpack200
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/lib
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/classlist
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jexec
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jrt-fs.jar
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/modules
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/psfont.properties.ja
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/psfontj2d.properties
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/tzdb.dat
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/lib/jli
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jli/libjli.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jvm.cfg
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libattach.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libawt.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libextnet.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjsig.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libawt_headless.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libdt_socket.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libfontmanager.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libinstrument.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libj2gss.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libj2pcsc.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libj2pkcs11.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjaas_unix.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjava.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjavajpeg.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjdwp.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjimage.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjsound.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/liblcms.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libmanagement.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libmanagement_agent.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libmanagement_ext.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libmlib_image.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libnet.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libnio.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libprefs.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/librmi.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libsaproc.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libsctp.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libsunec.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libunpack.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libverify.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libzip.so
%{_mandir}/man1/java-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jjs-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/keytool-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/orbd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/pack200-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmid-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmiregistry-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/servertool-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/tnameserv-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/unpack200-%{uniquesuffix -- %{?1}}.1*
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/server/
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/client/
%ifarch %{jit_arches}
%ifnarch %{power64}
%attr(444, root, root) %ghost %{_jvmdir}/%{sdkdir -- %{?1}}/lib/server/classes.jsa
%attr(444, root, root) %ghost %{_jvmdir}/%{sdkdir -- %{?1}}/lib/client/classes.jsa
%endif
%endif
%dir %{etcjavasubdir}
%dir %{etcjavadir -- %{?1}}
%dir %{etcjavadir -- %{?1}}/lib
%dir %{etcjavadir -- %{?1}}/lib/security
%{etcjavadir -- %{?1}}/lib/security/cacerts
%dir %{etcjavadir -- %{?1}}/conf
%dir %{etcjavadir -- %{?1}}/conf/management
%dir %{etcjavadir -- %{?1}}/conf/security
%dir %{etcjavadir -- %{?1}}/conf/security/policy
%dir %{etcjavadir -- %{?1}}/conf/security/policy/limited
%dir %{etcjavadir -- %{?1}}/conf/security/policy/unlimited
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/default.policy
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/blacklisted.certs
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/policy/limited/exempt_local.policy
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/policy/limited/default_local.policy
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/policy/limited/default_US_export.policy
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/policy/unlimited/default_local.policy
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/policy/unlimited/default_US_export.policy
 %{etcjavadir -- %{?1}}/conf/security/policy/README.txt
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/java.policy
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/java.security
%config(noreplace) %{etcjavadir -- %{?1}}/conf/logging.properties
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/nss.cfg
%config(noreplace) %{etcjavadir -- %{?1}}/conf/management/jmxremote.access
# this is conifg template, thus not config-noreplace
%config  %{etcjavadir -- %{?1}}/conf/management/jmxremote.password.template
%config(noreplace) %{etcjavadir -- %{?1}}/conf/management/management.properties
%config(noreplace) %{etcjavadir -- %{?1}}/conf/net.properties
%config(noreplace) %{etcjavadir -- %{?1}}/conf/sound.properties
%{_jvmdir}/%{sdkdir -- %{?1}}/conf
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/security
}

%define files_devel() %{expand:
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/bin
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/appletviewer
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/idlj
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jar
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jarsigner
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javac
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javadoc
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javap
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jconsole
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jcmd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jdb
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jdeps
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jdeprscan
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jimage
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jhsdb
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jinfo
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jlink
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jmap
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jmod
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jps
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jrunscript
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jshell
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstack
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstat
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstatd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmic
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/schemagen
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/serialver
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/wsgen
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/wsimport
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/xjc
%ifarch %{aot_arches}
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jaotc
%endif
%{_jvmdir}/%{sdkdir -- %{?1}}/include
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/ct.sym
%if %{with_systemtap}
%{_jvmdir}/%{sdkdir -- %{?1}}/tapset
%endif
%{_datadir}/applications/*jconsole%{?1}.desktop
%{_mandir}/man1/appletviewer-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/idlj-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jar-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jarsigner-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javac-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javadoc-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javap-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jconsole-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jcmd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jdb-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jdeps-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jinfo-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jmap-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jps-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jrunscript-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstack-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstat-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstatd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmic-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/schemagen-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/serialver-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/wsgen-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/wsimport-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/xjc-%{uniquesuffix -- %{?1}}.1*
%if %{with_systemtap}
%{tapsetdir}/*%{_arch}%{?1}.stp
%endif
}

%define files_jmods() %{expand:
%{_jvmdir}/%{sdkdir -- %{?1}}/jmods
}

%define files_demo() %{expand:
%license %{_jvmdir}/%{sdkdir -- %{?1}}/legal
%{_jvmdir}/%{sdkdir -- %{?1}}/demo
%{_jvmdir}/%{sdkdir -- %{?1}}/sample
}

%define files_src() %{expand:
%license %{_jvmdir}/%{sdkdir -- %{?1}}/legal
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/src.zip
}

%define files_javadoc() %{expand:
%doc %{_javadocdir}/%{uniquejavadocdir -- %{?1}}
%license %{buildoutputdir -- %{?1}}/images/%{jdkimage}/legal
}

%define files_javadoc_zip() %{expand:
%doc %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip
%license %{buildoutputdir -- %{?1}}/images/%{jdkimage}/legal
}

# not-duplicated requires/provides/obsoletes for normal/debug packages
%define java_rpo() %{expand:
Requires: fontconfig%{?_isa}
Requires: x11-font-type1
# Requires rest of java
Requires: %{name}-headless%{?1}%{?_isa} = %{EVRD}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{EVRD}

Provides: java-%{javaver}-%{origin}%{?1} = %{EVRD}

# Standard JPackage base provides
Provides: jre = %{javaver}%{?1}
Provides: jre-%{origin}%{?1} = %{EVRD}
Provides: jre-%{javaver}%{?1} = %{EVRD}
Provides: jre-%{javaver}-%{origin}%{?1} = %{EVRD}
Provides: java-%{javaver}%{?1} = %{EVRD}
Provides: java-%{origin}%{?1} = %{EVRD}
Provides: java%{?1} = %{javaver}
}

%define java_headless_rpo() %{expand:
# Require /etc/pki/java/cacerts
Requires: ca-certificates
# Require zone-info data provided by tzdata-java sub-package
Requires: tzdata-java >= 2015d
# libsctp.so.1 is being `dlopen`ed on demand
Requires: %{_lib}sctp1
# there is a need to depend on the exact version of NSS
Requires: nss%{?_isa} %{NSS_BUILDTIME_VERSION}
# Post requires alternatives to install tool alternatives
Requires(post):   %{_sbindir}/alternatives
# Postun requires alternatives to uninstall tool alternatives
Requires(postun): %{_sbindir}/alternatives

# Standard JPackage base provides
Provides: jre-headless%{?1} = %{javaver}
Provides: jre-%{javaver}-%{origin}-headless%{?1} = %{EVRD}
Provides: jre-%{origin}-headless%{?1} = %{EVRD}
Provides: jre-%{javaver}-headless%{?1} = %{EVRD}
Provides: java-%{javaver}-%{origin}-headless%{?1} = %{EVRD}
Provides: java-%{javaver}-headless%{?1} = %{EVRD}
Provides: java-%{origin}-headless%{?1} = %{EVRD}
Provides: java-headless%{?1} = %{javaver}

# https://bugzilla.redhat.com/show_bug.cgi?id=1312019
Provides: /usr/bin/jjs

}

%define java_devel_rpo() %{expand:
# Requires base package
Requires:         %{name}%{?1}%{?_isa} = %{EVRD}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{EVRD}
# Post requires alternatives to install tool alternatives
Requires(post):   %{_sbindir}/alternatives
# in version 1.7 and higher for --family switch
Requires(post):   chkconfig >= 1.7
# Postun requires alternatives to uninstall tool alternatives
Requires(postun): %{_sbindir}/alternatives
# in version 1.7 and higher for --family switch
Requires(postun):   chkconfig >= 1.7

# Standard JPackage devel provides
Provides: java-sdk-%{javaver}-%{origin}%{?1} = %{EVRD}
Provides: java-sdk-%{javaver}%{?1} = %{EVRD}
Provides: java-%{javaver}-devel%{?1} = %{EVRD}
Provides: java-%{javaver}-%{origin}-devel%{?1} = %{EVRD}
}

%define java_jmods_rpo() %{expand:
# Requires devel package
# as jmods are bytecode, they should be OK without any _isa
Requires:         %{name}-devel%{?1} = %{EVRD}
OrderWithRequires: %{name}-headless%{?1} = %{EVRD}

Provides: java-jmods%{?1} = %{EVRD}
Provides: java-%{javaver}-jmods%{?1} = %{EVRD}
Provides: java-%{javaver}-%{origin}-jmods%{?1} = %{EVRD}

}

%define java_demo_rpo() %{expand:
Requires: %{name}%{?1}%{?_isa} = %{EVRD}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{EVRD}

Provides: java-demo%{?1} = %{EVRD}
Provides: java-%{javaver}-demo%{?1} = %{EVRD}
Provides: java-%{javaver}-%{origin}-demo%{?1} = %{EVRD}

}

%define java_javadoc_rpo() %{expand:
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{EVRD}
# Post requires alternatives to install javadoc alternative
Requires(post):   %{_sbindir}/alternatives
# in version 1.7 and higher for --family switch
Requires(post):   chkconfig >= 1.7
# Postun requires alternatives to uninstall javadoc alternative
Requires(postun): %{_sbindir}/alternatives
# in version 1.7 and higher for --family switch
Requires(postun):   chkconfig >= 1.7

# Standard JPackage javadoc provides
Provides: java-javadoc%{?1} = %{EVRD}
Provides: java-%{javaver}-javadoc%{?1} = %{EVRD}
Provides: java-%{javaver}-%{origin}-javadoc%{?1} = %{EVRD}
}

%define java_src_rpo() %{expand:
Requires: %{name}-headless%{?1}%{?_isa} = %{EVRD}

# Standard JPackage sources provides
Provides: java-src%{?1} = %{EVRD}
Provides: java-%{javaver}-src%{?1} = %{EVRD}
Provides: java-%{javaver}-%{origin}-src%{?1} = %{EVRD}
}

# Prevent brp-java-repack-jars from being run
%global __jar_repack 0

Name:    java-%{majorver}-%{origin}
Version: %{newjavaver}.%{buildver}
Release: 2
Summary: %{origin_nice} Runtime Environment %{majorver}
Group:   Development/Languages

# HotSpot code is licensed under GPLv2
# JDK library code is licensed under GPLv2 with the Classpath exception
# The Apache license is used in code taken from Apache projects (primarily JAXP & JAXWS)
# DOM levels 2 & 3 and the XML digital signature schemas are licensed under the W3C Software License
# The JSR166 concurrency code is in the public domain
# The BSD and MIT licenses are used for a number of third-party libraries (see THIRD_PARTY_README)
# The OpenJDK source tree includes the JPEG library (IJG), zlib & libpng (zlib), giflib and LCMS (MIT)
# The test code includes copies of NSS under the Mozilla Public License v2.0
# The PCSClite headers are under a BSD with advertising license
# The elliptic curve cryptography (ECC) source code is licensed under the LGPLv2.1 or any later version
License:  ASL 1.1 and ASL 2.0 and BSD and BSD with advertising and GPL+ and GPLv2 and GPLv2 with exceptions and IJG and LGPLv2+ and MIT and MPLv2.0 and Public Domain and W3C and zlib
URL:      https://openjdk.java.net/


# to regenerate source0 (jdk) and source8 (jdk's taspets) run update_package.sh
# update_package.sh contains hard-coded repos, revisions, tags, and projects to regenerate the source archives
Source0: jdk-updates-jdk%{majorver}u-jdk-%{newjavaver}+%{buildver}.tar.xz
Source8: systemtap_3.2_tapsets_hg-icedtea8-9d464368e06d.tar.xz

# Desktop files. Adapted from IcedTea
Source9: jconsole.desktop.in

# nss configuration file
Source11: nss.cfg.in

# Removed libraries that we link instead
Source12: remove-intree-libraries.sh

# Ensure we aren't using the limited crypto policy
Source13: TestCryptoLevel.java

# Ensure ECDSA is working
Source14: TestECDSA.java

############################################
#
# RPM/distribution specific patches
#
############################################

# NSS via SunPKCS11 Provider (disabled comment
# due to memory leak).
Patch1000: enableCommentedOutSystemNss.patch

# Ignore AWTError when assistive technologies are loaded
Patch1:    accessible-toolkit.patch
# Restrict access to java-atk-wrapper classes
Patch2:    java-atk-wrapper-security.patch
Patch3:    libjpeg-turbo-1.4-compat.patch
# Follow system wide crypto policy RHBZ#1249083
Patch4:    RHBZ-1249083-system-crypto-policy-PR3183.patch
# System NSS via SunEC Provider
Patch5:    RHBZ-1565658-system-nss-SunEC.patch

Patch6:    openjdk-10-clang.patch

#############################################
#
# OpenJDK specific patches
#
#############################################

# s390 (Zero) build does not bootcycle without this patch
# Already in JDK-11. Missing backports.
Patch100:  JDK-8201495-s390-java-opts.patch
# See JDK-8198844. This won't be needed any more in
# JDK 11+
Patch101:  sorted-diff.patch
# Type fixing for s390 (Zero). Not upstream.
Patch102:  java-openjdk-s390-size_t.patch
# Fix https://bugs.openjdk.java.net/browse/JDK-8203223
Patch103:  http://hg.openjdk.java.net/jdk/jdk/raw-rev/2d9dd2b876a0
# Fix https://bugs.openjdk.java.net/browse/JDK-8207044
Patch104:  http://hg.openjdk.java.net/jdk/jdk11/raw-rev/46d206233051

BuildRequires: autoconf
BuildRequires: automake
BuildRequires: pkgconfig(alsa)
BuildRequires: binutils
BuildRequires: cups-devel
BuildRequires: desktop-file-utils
# elfutils only are OK for build without AOT
BuildRequires: elfutils-devel
BuildRequires: fontconfig
BuildRequires: freetype-devel
BuildRequires: giflib-devel
BuildRequires: gcc-c++
BuildRequires: gdb
BuildRequires: pkgconfig(gtk+-x11-3.0)
BuildRequires: pkgconfig(lcms2)
BuildRequires: pkgconfig(libjpeg)
BuildRequires: pkgconfig(libpng)
BuildRequires: pkgconfig(libxslt)
BuildRequires: pkgconfig(x11)
BuildRequires: pkgconfig(xi)
BuildRequires: pkgconfig(xinerama)
BuildRequires: pkgconfig(xt)
BuildRequires: pkgconfig(xtst)
# Requirements for setting up the nss.cfg
BuildRequires: pkgconfig(nss)
BuildRequires: pkgconfig(nss-softokn)
# For freebl
BuildRequires: nss-static-devel
BuildRequires: pkgconfig
BuildRequires: x11-proto-devel
BuildRequires: zip
BuildRequires: java-9-openjdk-devel
# Zero-assembler build requirement
%ifnarch %{jit_arches}
BuildRequires: libffi-devel
%endif
BuildRequires: tzdata-java >= 2015d

%if %{with_systemtap}
BuildRequires: systemtap-devel
%endif

# this is always built, also during debug-only build
# when it is built in debug-only this package is just placeholder
%{java_rpo %{nil}}

%description
The %{origin_nice} runtime environment.

%if %{include_debug_build}
%package slowdebug
Summary: %{origin_nice} Runtime Environment %{majorver} %{debug_on}
Group:   Development/Languages

%{java_rpo -- %{debug_suffix_unquoted}}
%description slowdebug
The %{origin_nice} runtime environment.
%{debug_warning}
%endif

%if %{include_normal_build}
%package headless
Summary: %{origin_nice} Headless Runtime Environment %{majorver}
Group:   Development/Languages

%{java_headless_rpo %{nil}}

%description headless
The %{origin_nice} runtime environment %{majorver} without audio and video support.
%endif

%if %{include_debug_build}
%package headless-slowdebug
Summary: %{origin_nice} Runtime Environment %{debug_on}
Group:   Development/Languages

%{java_headless_rpo -- %{debug_suffix_unquoted}}

%description headless-slowdebug
The %{origin_nice} runtime environment %{majorver} without audio and video support.
%{debug_warning}
%endif

%if %{include_normal_build}
%package devel
Summary: %{origin_nice} Development Environment %{majorver}
Group:   Development/Tools

%{java_devel_rpo %{nil}}

%description devel
The %{origin_nice} development tools %{majorver}.
%endif

%if %{include_debug_build}
%package devel-slowdebug
Summary: %{origin_nice} Development Environment %{majorver} %{debug_on}
Group:   Development/Tools

%{java_devel_rpo -- %{debug_suffix_unquoted}}

%description devel-slowdebug
The %{origin_nice} development tools %{majorver}.
%{debug_warning}
%endif

%if %{include_normal_build}
%package jmods
Summary: JMods for %{origin_nice} %{majorver}
Group:   Development/Tools

%{java_jmods_rpo %{nil}}

%description jmods
The JMods for %{origin_nice}.
%endif

%if %{include_debug_build}
%package jmods-slowdebug
Summary: JMods for %{origin_nice} %{majorver} %{debug_on}
Group:   Development/Tools

%{java_jmods_rpo -- %{debug_suffix_unquoted}}

%description jmods-slowdebug
The JMods for %{origin_nice} %{majorver}.
%{debug_warning}
%endif

%if %{include_normal_build}
%package demo
Summary: %{origin_nice} Demos %{majorver}
Group:   Development/Languages

%{java_demo_rpo %{nil}}

%description demo
The %{origin_nice} demos %{majorver}.
%endif

%if %{include_debug_build}
%package demo-slowdebug
Summary: %{origin_nice} Demos %{majorver} %{debug_on}
Group:   Development/Languages

%{java_demo_rpo -- %{debug_suffix_unquoted}}

%description demo-slowdebug
The %{origin_nice} demos %{majorver}.
%{debug_warning}
%endif

%if %{include_normal_build}
%package src
Summary: %{origin_nice} Source Bundle %{majorver}
Group:   Development/Languages

%{java_src_rpo %{nil}}

%description src
The java-%{origin}-src sub-package contains the complete %{origin_nice} %{majorver}
class library source code for use by IDE indexers and debuggers.
%endif

%if %{include_debug_build}
%package src-slowdebug
Summary: %{origin_nice} Source Bundle %{majorver} %{for_debug}
Group:   Development/Languages

%{java_src_rpo -- %{debug_suffix_unquoted}}

%description src-slowdebug
The java-%{origin}-src-slowdebug sub-package contains the complete %{origin_nice} %{majorver}
 class library source code for use by IDE indexers and debuggers. Debugging %{for_debug}.
%endif

%if %{include_normal_build}
%package javadoc
Summary: %{origin_nice} %{majorver} API documentation
Group:   Documentation

%{java_javadoc_rpo %{nil}}

%description javadoc
The %{origin_nice} %{majorver} API documentation.
%endif

%if %{include_normal_build}
%package javadoc-zip
Summary: %{origin_nice} %{majorver} API documentation compressed in single archive
Group:   Documentation

%{java_javadoc_rpo %{nil}}

%description javadoc-zip
The %{origin_nice} %{majorver} API documentation compressed in single archive.
%endif

%if %{include_debug_build}
%package javadoc-slowdebug
Summary: %{origin_nice} %{majorver} API documentation %{for_debug}
Group:   Documentation

%{java_javadoc_rpo -- %{debug_suffix_unquoted}}

%description javadoc-slowdebug
The %{origin_nice} %{majorver} API documentation %{for_debug}.
%endif

%if %{include_debug_build}
%package javadoc-zip-slowdebug
Summary: %{origin_nice} %{majorver} API documentation compressed in single archive %{for_debug}
Group:   Documentation

%{java_javadoc_rpo -- %{debug_suffix_unquoted}}

%description javadoc-zip-slowdebug
The %{origin_nice} %{majorver} API documentation compressed in single archive %{for_debug}.
%endif


%prep
if [ %{include_normal_build} -eq 0 -o  %{include_normal_build} -eq 1 ] ; then
  echo "include_normal_build is %{include_normal_build}"
else
  echo "include_normal_build is %{include_normal_build}, thats invalid. Use 1 for yes or 0 for no"
  exit 11
fi
if [ %{include_debug_build} -eq 0 -o  %{include_debug_build} -eq 1 ] ; then
  echo "include_debug_build is %{include_debug_build}"
else
  echo "include_debug_build is %{include_debug_build}, thats invalid. Use 1 for yes or 0 for no"
  exit 12
fi
if [ %{include_debug_build} -eq 0 -a  %{include_normal_build} -eq 0 ] ; then
  echo "You have disabled both include_debug_build and include_normal_build. That is a no go."
  exit 13
fi
%setup -q -c -n %{uniquesuffix ""} -T -a 0
# https://bugzilla.redhat.com/show_bug.cgi?id=1189084
prioritylength=`expr length %{priority}`
if [ $prioritylength -ne 7 ] ; then
 echo "priority must be 7 digits in total, violated"
 exit 14
fi

# OpenJDK patches

pushd %{top_level_dir_name}
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1

#ifarch %{arm}
# NOT YET: while it fixes clang, it breaks gcc
#patch6 -p1
#endif

%patch101 -p1
%patch102 -p1
%patch103 -p1
%patch104 -p1

popd # openjdk

%patch1000

# Extract systemtap tapsets
%if %{with_systemtap}
tar --strip-components=1 -xf %{SOURCE8}
%if %{include_debug_build}
cp -r tapset tapset%{debug_suffix}
%endif


for suffix in %{build_loop} ; do
  for file in "tapset"$suffix/*.in; do
    OUTPUT_FILE=`echo $file | sed -e "s:\.stp\.in$:%{version}-%{release}.%{_arch}.stp:g"`
    sed -e "s:@ABS_SERVER_LIBJVM_SO@:%{_jvmdir}/%{sdkdir -- $suffix}/lib/server/libjvm.so:g" $file > $file.1
# TODO find out which architectures other than i686 have a client vm
%ifarch %{ix86}
    sed -e "s:@ABS_CLIENT_LIBJVM_SO@:%{_jvmdir}/%{sdkdir -- $suffix}/lib/client/libjvm.so:g" $file.1 > $OUTPUT_FILE
%else
    sed -e "/@ABS_CLIENT_LIBJVM_SO@/d" $file.1 > $OUTPUT_FILE
%endif
    sed -i -e "s:@ABS_JAVA_HOME_DIR@:%{_jvmdir}/%{sdkdir -- $suffix}:g" $OUTPUT_FILE
    sed -i -e "s:@INSTALL_ARCH_DIR@:%{archinstall}:g" $OUTPUT_FILE
    sed -i -e "s:@prefix@:%{_jvmdir}/%{sdkdir -- $suffix}/:g" $OUTPUT_FILE
  done
done
# systemtap tapsets ends
%endif

# Prepare desktop files
for suffix in %{build_loop} ; do
for file in %{SOURCE9}; do
    FILE=`basename $file | sed -e s:\.in$::g`
    EXT="${FILE##*.}"
    NAME="${FILE%.*}"
    OUTPUT_FILE=$NAME$suffix.$EXT
    sed    -e  "s:@JAVA_HOME@:%{sdkbindir -- $suffix}:g" $file > $OUTPUT_FILE
    sed -i -e  "s:@JRE_HOME@:%{jrebindir -- $suffix}:g" $OUTPUT_FILE
    sed -i -e  "s:@ARCH@:%{version}-%{release}.%{_arch}$suffix:g" $OUTPUT_FILE
    sed -i -e  "s:@JAVA_MAJOR_VERSION@:%{majorver}:g" $OUTPUT_FILE
    sed -i -e  "s:@JAVA_VENDOR@:%{origin}:g" $OUTPUT_FILE
done
done

# Setup nss.cfg
sed -e "s:@NSS_LIBDIR@:%{NSS_LIBDIR}:g" %{SOURCE11} > nss.cfg


%build
# How many CPU's do we have?
export NUM_PROC=%(/usr/bin/getconf _NPROCESSORS_ONLN 2> /dev/null || :)
export NUM_PROC=${NUM_PROC:-1}
%if 0%{?_smp_ncpus_max}
# Honor %%_smp_ncpus_max
[ ${NUM_PROC} -gt %{?_smp_ncpus_max} ] && export NUM_PROC=%{?_smp_ncpus_max}
%endif

%ifarch s390x sparc64 alpha %{power64} %{aarch64}
export ARCH_DATA_MODEL=64
%endif
%ifarch alpha
export CFLAGS="$CFLAGS -mieee"
%endif

# We use ourcppflags because the OpenJDK build seems to
# pass EXTRA_CFLAGS to the HotSpot C++ compiler...
# Explicitly set the C++ standard as the default has changed on GCC >= 6
EXTRA_CFLAGS="%ourcppflags -Wno-error -fno-delete-null-pointer-checks"
EXTRA_CPP_FLAGS="%ourcppflags -std=gnu++98 -fno-delete-null-pointer-checks"
%ifnarch %{arm}
EXTRA_CFLAGS="$EXTRA_CFLAGS -std=gnu++98 -fno-lifetime-dse"
EXTRA_CPP_FLAGS="$EXTRA_CPP_FLAGS -fno-lifetime-dse"
%endif

%ifarch %{ix86}
EXTRA_CFLAGS="$EXTRA_CFLAGS -mincoming-stack-boundary=2"
EXTRA_CPP_FLAGS="$EXTRA_CPP_FLAGS -mincoming-stack-boundary=2"
%endif

%ifarch %{power64} ppc
# fix rpmlint warnings
EXTRA_CFLAGS="$EXTRA_CFLAGS -fno-strict-aliasing"
%endif
export EXTRA_CFLAGS

(cd %{top_level_dir_name}/make/autoconf
 bash ./autogen.sh
)

for suffix in %{build_loop} ; do
if [ "x$suffix" = "x" ] ; then
  debugbuild=release
else
  # change --something to something
  debugbuild=`echo $suffix  | sed "s/-//g"`
fi

# Variable used in hs_err hook on build failures
top_dir_abs_path=$(pwd)/%{top_level_dir_name}

mkdir -p %{buildoutputdir -- $suffix}
pushd %{buildoutputdir -- $suffix}

if ! bash ../configure \
%ifnarch %{jit_arches}
    --with-jvm-variants=zero \
%endif
%ifarch %{ppc64le}
    --with-jobs=1 \
%endif
    --with-version-build=%{buildver} \
    --with-version-pre="" \
    --with-version-opt="" \
    --with-boot-jdk=$(ls -d /usr/lib/jvm/java-9-openjdk-* |head -n1) \
    --with-debug-level=$debugbuild \
    --with-native-debug-symbols=internal \
    --enable-unlimited-crypto \
    --enable-system-nss \
    --with-zlib=system \
    --with-libjpeg=system \
    --with-giflib=system \
    --with-libpng=system \
    --with-lcms=system \
    --with-stdc++lib=dynamic \
    --with-extra-cxxflags="$EXTRA_CPP_FLAGS" \
    --with-extra-cflags="$EXTRA_CFLAGS" \
    --with-extra-ldflags="%{ourldflags}" \
    --with-num-cores="$NUM_PROC" \
    --disable-javac-server \
    --disable-warnings-as-errors \
	; then
	echo 'configure failed -- log:'
	cat config.log
	exit 1
fi

make \
    JOBS=$(getconf _NPROCESSORS_ONLN) \
    JAVAC_FLAGS=-g \
    LOG=trace \
    WARNINGS_ARE_ERRORS="-Wno-error" \
    CFLAGS_WARNINGS_ARE_ERRORS="-Wno-error" \
    %{targets} || ( pwd; find $top_dir_abs_path -name "hs_err_pid*.log" | xargs cat && false )

make \
    JOBS=$(getconf _NPROCESSORS_ONLN) \
    docs-zip

# the build (erroneously) removes read permissions from some jars
# this is a regression in OpenJDK 7 (our compiler):
# http://icedtea.classpath.org/bugzilla/show_bug.cgi?id=1437
find images/%{jdkimage} -iname '*.jar' -exec chmod ugo+r {} \;

# remove redundant *diz and *debuginfo files
find images/%{jdkimage} -iname '*.diz' -exec rm {} \;
find images/%{jdkimage} -iname '*.debuginfo' -exec rm {} \;

# Build screws up permissions on binaries
# https://bugs.openjdk.java.net/browse/JDK-8173610
find images/%{jdkimage} -iname '*.so' -exec chmod +x {} \;
find images/%{jdkimage}/bin/ -exec chmod +x {} \;

popd >& /dev/null

# Install nss.cfg right away as we will be using the JRE above
export JAVA_HOME=$(pwd)/%{buildoutputdir -- $suffix}/images/%{jdkimage}

# Install nss.cfg right away as we will be using the JRE above
install -m 644 nss.cfg $JAVA_HOME/conf/security/
# build cycles
done

%check

# We test debug first as it will give better diagnostics on a crash
for suffix in %{rev_build_loop} ; do

export JAVA_HOME=$(pwd)/%{buildoutputdir -- $suffix}/images/%{jdkimage}

# Check unlimited policy has been used
$JAVA_HOME/bin/javac -d . %{SOURCE13}
$JAVA_HOME/bin/java --add-opens java.base/javax.crypto=ALL-UNNAMED TestCryptoLevel

# Check ECC is working
$JAVA_HOME/bin/javac -d . %{SOURCE14}
$JAVA_HOME/bin/java $(echo $(basename %{SOURCE14})|sed "s|\.java||")

# Check debug symbols are present and can identify code
find "$JAVA_HOME" -iname '*.so' -print0 | while read -d $'\0' lib
do
  if [ -f "$lib" ] ; then
    echo "Testing $lib for debug symbols"
    # All these tests rely on RPM failing the build if the exit code of any set
    # of piped commands is non-zero.

    # Test for .debug_* sections in the shared object. This is the main test
    # Stripped objects will not contain these
    eu-readelf -S "$lib" | grep "] .debug_"
    test $(eu-readelf -S "$lib" | grep -E "\]\ .debug_(info|abbrev)" | wc --lines) == 2

    # LTO tends to break the following test, so we disable it
%if 0
    # Test FILE symbols. These will most likely be removed by anything that
    # manipulates symbol tables because it's generally useless. So a nice test
    # that nothing has messed with symbols
    old_IFS="$IFS"
    IFS=$'\n'
    for line in $(eu-readelf -s "$lib" | grep "00000000      0 FILE    LOCAL  DEFAULT")
    do
     # We expect to see .cpp files, except for architectures like aarch64 and
     # s390 where we expect .o and .oS files
      echo "$line" | grep -E "ABS ((.*/)?[-_a-zA-Z0-9]+\.(c|cc|cpp|cxx|o|oS))?$"
    done
    IFS="$old_IFS"
%endif

    # If this is the JVM, look for javaCalls.(cpp|o) in FILEs, for extra sanity checking
    if [ "`basename $lib`" = "libjvm.so" ]; then
      eu-readelf -s "$lib" | \
        grep -E "00000000      0 FILE    LOCAL  DEFAULT      ABS javaCalls.(cpp|o)$"
    fi

    # Test that there are no .gnu_debuglink sections pointing to another
    # debuginfo file. There shouldn't be any debuginfo files, so the link makes
    # no sense either
    eu-readelf -S "$lib" | grep 'gnu'
    if eu-readelf -S "$lib" | grep '] .gnu_debuglink' | grep PROGBITS; then
      echo "bad .gnu_debuglink section."
      eu-readelf -x .gnu_debuglink "$lib"
      false
    fi
  fi
done

# This tends to run out of memory on 32-bit platforms
# BUILDSTDERR: Error in re-setting breakpoint 1: virtual memory exhausted: can't allocate 4064 bytes. [...]
# So let's limit this test to 64-bit platforms for now
%ifarch %{x86_64} %{aarch64}
# Make sure gdb can do a backtrace based on line numbers on libjvm.so
# javaCalls.cpp:58 should map to:
# http://hg.openjdk.java.net/jdk8u/jdk8u/hotspot/file/ff3b27e6bcc2/src/share/vm/runtime/javaCalls.cpp#l58 
# Using line number 1 might cause build problems. See:
# https://bugzilla.redhat.com/show_bug.cgi?id=1539664
# https://bugzilla.redhat.com/show_bug.cgi?id=1538767
gdb -q "$JAVA_HOME/bin/java" <<EOF | tee gdb.out
handle SIGSEGV pass nostop noprint
handle SIGILL pass nostop noprint
set breakpoint pending on
break javaCalls.cpp:1
commands 1
backtrace
quit
end
run -version
EOF
grep 'JavaCallWrapper::JavaCallWrapper' gdb.out
%endif

# Check src.zip has all sources. See RHBZ#1130490
jar -tf $JAVA_HOME/lib/src.zip | grep 'sun.misc.Unsafe'

# Check class files include useful debugging information
$JAVA_HOME/bin/javap -l java.lang.Object | grep "Compiled from"
$JAVA_HOME/bin/javap -l java.lang.Object | grep LineNumberTable
$JAVA_HOME/bin/javap -l java.lang.Object | grep LocalVariableTable

# Check generated class files include useful debugging information
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep "Compiled from"
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LineNumberTable
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LocalVariableTable

# build cycles check
done

%install
STRIP_KEEP_SYMTAB=libjvm*

for suffix in %{build_loop} ; do

# Install the jdk
mkdir -p $RPM_BUILD_ROOT%{_jvmdir}
cp -a %{buildoutputdir -- $suffix}/images/%{jdkimage} \
  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}

# Install jsa directories so we can owe them
mkdir -p $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/lib/%{archinstall}/server/
mkdir -p $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/lib/%{archinstall}/client/
mkdir -p $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/lib/client/ || true  ; # sometimes is here, sometimes not, ifout it or || true it out

pushd %{buildoutputdir $suffix}/images/%{jdkimage}

%if %{with_systemtap}
  # Install systemtap support files
  install -dm 755 $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset
  # note, that uniquesuffix  is in BUILD dir in this case
  cp -a $RPM_BUILD_DIR/%{uniquesuffix ""}/tapset$suffix/*.stp $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset/
  pushd  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset/
   tapsetFiles=`ls *.stp`
  popd
  install -d -m 755 $RPM_BUILD_ROOT%{tapsetdir}
  for name in $tapsetFiles ; do
    targetName=`echo $name | sed "s/.stp/$suffix.stp/"`
    ln -sf %{_jvmdir}/%{sdkdir -- $suffix}/tapset/$name $RPM_BUILD_ROOT%{tapsetdir}/$targetName
  done
%endif

  # Remove empty cacerts database
  rm -f $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/lib/security/cacerts
  # Install cacerts symlink needed by some apps which hard-code the path
  pushd $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/lib/security
      ln -sf /etc/pki/java/cacerts .
  popd

  # Install version-ed symlinks
  pushd $RPM_BUILD_ROOT%{_jvmdir}
    ln -sf %{sdkdir -- $suffix} %{jrelnk -- $suffix}
  popd


  # Install man pages
  install -d -m 755 $RPM_BUILD_ROOT%{_mandir}/man1
  for manpage in man/man1/*
  do
    # Convert man pages to UTF8 encoding
    iconv -f ISO_8859-1 -t UTF8 $manpage -o $manpage.tmp
    mv -f $manpage.tmp $manpage
    install -m 644 -p $manpage $RPM_BUILD_ROOT%{_mandir}/man1/$(basename \
      $manpage .1)-%{uniquesuffix -- $suffix}.1
  done
  # Remove man pages from jdk image
  rm -rf $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/man

popd


# Install Javadoc documentation
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}
cp -a %{buildoutputdir -- $suffix}/images/docs $RPM_BUILD_ROOT%{_javadocdir}/%{uniquejavadocdir -- $suffix}
cp -a %{buildoutputdir -- $suffix}/bundles/jdk-%{newjavaver}+%{buildver}-docs.zip  $RPM_BUILD_ROOT%{_javadocdir}/%{uniquejavadocdir -- $suffix}.zip

# Install icons and menu entries
for s in 16 24 32 48 ; do
  install -D -p -m 644 \
    %{top_level_dir_name}/src/java.desktop/unix/classes/sun/awt/X11/java-icon${s}.png \
    $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/${s}x${s}/apps/java-%{javaver}-%{origin}.png
done

# Install desktop files
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/{applications,pixmaps}
for e in jconsole$suffix ; do
    desktop-file-install --vendor=%{uniquesuffix -- $suffix} --mode=644 \
        --dir=$RPM_BUILD_ROOT%{_datadir}/applications $e.desktop
done

# Install /etc/.java/.systemPrefs/ directory
# See https://bugzilla.redhat.com/show_bug.cgi?id=741821
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/.java/.systemPrefs

# FIXME: remove SONAME entries from demo DSOs. See
# https://bugzilla.redhat.com/show_bug.cgi?id=436497

# copy samples next to demos; samples are mostly js files
cp -r %{top_level_dir_name}/src/sample  $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/


# moving config files to /etc
mkdir -p $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}
mkdir -p $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}/lib
mv $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/conf/  $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}
mv $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/lib/security  $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}/lib
pushd $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}
  ln -s %{etcjavadir -- $suffix}/conf  ./conf
popd
pushd $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/lib
  ln -s %{etcjavadir -- $suffix}/lib/security  ./security
popd
# end moving files to /etc

# stabilize permissions
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/ -name "*.so" -exec chmod 755 {} \; ; 
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/ -type d -exec chmod 755 {} \; ; 
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/legal -type f -exec chmod 644 {} \; ; 

# end, dual install
done

%if %{include_normal_build}
# intentionally only for non-debug
%pretrans headless -p <lua>
-- see https://bugzilla.redhat.com/show_bug.cgi?id=1038092 for whole issue
-- see https://bugzilla.redhat.com/show_bug.cgi?id=1290388 for pretrans over pre
-- if copy-jdk-configs is in transaction, it installs in pretrans to temp
-- if copy_jdk_configs is in temp, then it means that copy-jdk-configs is in transaction  and so is
-- preferred over one in %%{_libexecdir}. If it is not in transaction, then depends
-- whether copy-jdk-configs is installed or not. If so, then configs are copied
-- (copy_jdk_configs from %%{_libexecdir} used) or not copied at all
local posix = require "posix"
local debug = false

SOURCE1 = "%{rpm_state_dir}/copy_jdk_configs.lua"
SOURCE2 = "%{_libexecdir}/copy_jdk_configs.lua"

local stat1 = posix.stat(SOURCE1, "type");
local stat2 = posix.stat(SOURCE2, "type");

  if (stat1 ~= nil) then
  if (debug) then
    print(SOURCE1 .." exists - copy-jdk-configs in transaction, using this one.")
  end;
  package.path = package.path .. ";" .. SOURCE1
else
  if (stat2 ~= nil) then
  if (debug) then
    print(SOURCE2 .." exists - copy-jdk-configs already installed and NOT in transaction. Using.")
  end;
  package.path = package.path .. ";" .. SOURCE2
  else
    if (debug) then
      print(SOURCE1 .." does NOT exists")
      print(SOURCE2 .." does NOT exists")
      print("No config files will be copied")
    end
  return
  end
end
-- run content of included file with fake args
arg = {"--currentjvm", "%{uniquesuffix %{nil}}", "--jvmdir", "%{_jvmdir %{nil}}", "--origname", "%{name}", "--origjavaver", "%{javaver}", "--arch", "%{_arch}", "--temp", "%{rpm_state_dir}/%{name}.%{_arch}"}
require "copy_jdk_configs.lua"

%post
%{post_script %{nil}}

%post headless
%{post_headless %{nil}}

%postun
%{postun_script %{nil}}

%postun headless
%{postun_headless %{nil}}

%posttrans
%{posttrans_script %{nil}}

%post devel
%{post_devel %{nil}}

%postun devel
%{postun_devel %{nil}}

%posttrans  devel
%{posttrans_devel %{nil}}

%post javadoc
%{post_javadoc %{nil}}

%postun javadoc
%{postun_javadoc %{nil}}

%post javadoc-zip
%{post_javadoc_zip %{nil}}

%postun javadoc-zip
%{postun_javadoc_zip %{nil}}
%endif

%if %{include_debug_build}
%post slowdebug
%{post_script -- %{debug_suffix_unquoted}}

%post headless-slowdebug
%{post_headless -- %{debug_suffix_unquoted}}

%postun slowdebug
%{postun_script -- %{debug_suffix_unquoted}}

%postun headless-slowdebug
%{postun_headless -- %{debug_suffix_unquoted}}

%posttrans slowdebug
%{posttrans_script -- %{debug_suffix_unquoted}}

%post devel-slowdebug
%{post_devel -- %{debug_suffix_unquoted}}

%postun devel-slowdebug
%{postun_devel -- %{debug_suffix_unquoted}}

%posttrans  devel-slowdebug
%{posttrans_devel -- %{debug_suffix_unquoted}}

%post javadoc-slowdebug
%{post_javadoc -- %{debug_suffix_unquoted}}

%postun javadoc-slowdebug
%{postun_javadoc -- %{debug_suffix_unquoted}}

%post javadoc-zip-slowdebug
%{post_javadoc_zip -- %{debug_suffix_unquoted}}

%postun javadoc-zip-slowdebug
%{postun_javadoc_zip -- %{debug_suffix_unquoted}}
%endif

%if %{include_normal_build}
%files
# main package builds always
%{files_jre %{nil}}
%else
%files
# placeholder
%endif


%if %{include_normal_build}
%files headless
# important note, see https://bugzilla.redhat.com/show_bug.cgi?id=1038092 for whole issue
# all config/noreplace files (and more) have to be declared in pretrans. See pretrans
%{files_jre_headless %{nil}}

%files devel
%{files_devel %{nil}}

%files jmods
%{files_jmods %{nil}}

%files demo
%{files_demo %{nil}}

%files src
%{files_src %{nil}}

%files javadoc
%{files_javadoc %{nil}}

# this puts huge file to /usr/share
# unluckily ti is really a documentation file
# and unluckily it really is architecture-dependent, as eg. aot and grail are now x86_64 only
# same for debug variant
%files javadoc-zip
%{files_javadoc_zip %{nil}}
%endif

%if %{include_debug_build}
%files slowdebug
%{files_jre -- %{debug_suffix_unquoted}}

%files headless-slowdebug
%{files_jre_headless -- %{debug_suffix_unquoted}}

%files devel-slowdebug
%{files_devel -- %{debug_suffix_unquoted}}

%files jmods-slowdebug
%{files_jmods -- %{debug_suffix_unquoted}}

%files demo-slowdebug
%{files_demo -- %{debug_suffix_unquoted}}

%files src-slowdebug
%{files_src -- %{debug_suffix_unquoted}}

%files javadoc-slowdebug
%{files_javadoc -- %{debug_suffix_unquoted}}

%files javadoc-zip-slowdebug
%{files_javadoc_zip -- %{debug_suffix_unquoted}}
%endif
