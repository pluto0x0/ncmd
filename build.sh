echo please input version name:
read version
_ver=${version//./_}
filename="NCMdownload_v${_ver}.zip"
filename_unpack="NCMdownload_v${_ver}_unpacked.zip"

echo removing..
rm -rf dist/*

echo building packed release:
echo [PACKED] $version : `date` >> build.log
pyinstaller -Fw my.py -i icon.ico &>> build.log
echo ok

echo building unpacked release:
echo [UNPACKED] $version : `date` >> build.log
pyinstaller -w my.py -i icon.ico &>> build.log
echo ok

# see https://blog.csdn.net/MAO_SHUO/article/details/104360423
echo copy and rename files..
mv dist/my/ dist/ncmd/
mv dist/my.exe dist/ncmd.exe
mv dist/ncmd/my.exe dist/ncmd/ncmd.exe
cp aria2c.exe dist/ncmd/
cp aria2.conf dist/ncmd/
echo build zip file..
./zip -q -j ${filename} dist/ncmd.exe aria2c.exe aria2.conf
cd dist
../zip -r -q ../${filename_unpack} ncmd/
cd ..
echo ok

putMD5(){
    md5=`md5sum ${filename}`
    out=`expr substr "\"${md5}\"" 2 32`
    echo -n $out
}

echo  '📂|单文件版|未打包版' > sample.md
echo '---|---|---' >> sample.md
echo "🔗|[下载地址](https://github.com/pluto0x0/ncmd/releases/download/${version}/${filename})| [下载地址](https://github.com/pluto0x0/ncmd/releases/download/${version}/${filename_unpack})" >> sample.md
echo -n 'md5|' >> sample.md
putMD5 $filename >> sample.md
echo -n '|' >> sample.md
putMD5 $filename_unpack >> sample.md
echo '|' >> sample.md
echo '**（windows only）**' >> sample.md