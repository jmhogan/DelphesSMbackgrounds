### ERROR CHECKER for Delphes when running on GEN files (not snowmass LHE)
###
### Run like:
### python -u CheckErrorsDelphesGEN.py ~/nobackup/YR_Delphes/Delphes342pre13_logs/ --OPTION --OPTION
###
### Options:
###    --pileup 0PU, --pileup 200PU
###    --verbose 0 (quiet), --verbose 1 (print things)
###    --resubmit 0 (just check status), --resubmit 1 (resubmit failed jobs)
###    --resub_num -1 (resubmit all fails), --resub_num 0 (xrdcp fail), --resub_num 1 (walltime fail),
###    --resub_num 2 (root file with size zero), --resub_num 3 (no root file)


import os, sys, getopt,subprocess
execfile("/uscms_data/d3/jmanagan/UpgradeStudies/DelphesSMbackgrounds/EOSSafeUtils.py")
dir = sys.argv[1]

print; print 'Checking logs in', dir

try:
    opts, args = getopt.getopt(sys.argv[2:], "", ["verbose=", "resubmit=", "resub_num=", "pileup="])
except getopt.GetoptError as err:
    print str(err)
    sys.exit(1)

verbose_level = 0
resubmit = '0'
resub_num = -2
doNoLog = False
pileup = '0PU'

for o, a in opts:
	print o, a
	if o == '--verbose': verbose_level = int(a)
	if o == '--resubmit': resubmit = a
	if o == '--resub_num': resub_num = int(a)
        if o == '--pileup': pileup = str(a)

print 'Pileup setting:',pileup
#rootdir = '/eos/uscms/store/user/snowmass/noreplica/YR_Delphes/'+dir.split('/')[-2]+'/'
rootdir = '/store/group/upgrade/delphes_output/YR_Delphes/'+dir.split('/')[-2]+'/'
#rootdir = rootdir.replace('_logs_batch-02','')
rootdir = rootdir.replace('_logs','')
print 'checking ROOT files in:',rootdir
folders = [x for x in os.walk(dir).next()[1]]

total_total = 0
total_succeeded = 0
total_error = 0
total_running = 0
total_roots = 0

no_roots = 0
size_fail = 0
copy_fail = 0
time_fail = 0

for folder in folders:

    #to exclude one or more processes:
    #if 'TTTW_' not in folder: continue
    # don't resubmit
    # if 'ST_s-channel_4f_InclusiveDecays' in folder: continue
    # if 'ST_tW_antitop_5f_inclusiveDecays' in folder: continue
    # if 'TTWJetsToLNu' in folder: continue
    # if 'TT_TuneCUETP8M2T4_14TeV-powheg-pythia8-GenJetPt-950GeV' in folder: continue
    # if 'ZJetsToNuNu_HT-100To200' in folder: continue
    # if 'ZJetsToNuNu_HT-200To400' in folder: continue
    # if 'WW_TuneCUETP8M1' in folder: continue
    #if 'DiPhotonJetsBox' not in folder and 'THQ_Hincl' not in folder and 'VBF_LFV_HToMuTau' not in folder and 'ttHTobb_M125' not in folder and 'RSGluonToTTbar' not in folder and 'TT_Mtt1000toInf' not in folder and 'WWG' not in folder and 'ZZTo4L' not in folder: continue

    if pileup == '200PU' and '_200PU' not in folder:
        print 'skipping',folder,', pileup was',pileup
        continue
    if pileup == '140PU' and '_140PU' not in folder:
        print 'skipping',folder,', pileup was', pileup
        continue
    if pileup == '0PU' and '_0PU' not in folder:
        print 'skipping',folder,', pileup was', pileup
        continue

    print; print folder

    #rootfiles = EOSlist_root_files(rootdir+folder)
    rootfiles = GFALlist_root_files(rootdir+folder)
    total_roots += len(rootfiles)

    files = [x for x in os.listdir(dir+'/'+folder) if '.jdl' in x]

    os.listdir(dir+'/'+folder)

    resub_index = []
    resub_index_walltime = []
    count_total = 0
    finished = 0
    for file in files:
        total_total+=1
        index = file[file.find('_')+1:file.find('.')]
        #if '_' in index: index = index.split('_')[-1]
        if '_' in index: index = index.split('_')[-2]+'_'+index.split('_')[-1]  ## make split submission the default
        count_total += 1

        try:
            current = open(dir + '/'+folder+'/'+file.replace('.jdl','.out'),'r')
            copyfail = False
            transferfail = False
            delphesfail = False
            for line in current:
                if 'failure in xrdcp of MinBias' in line: copyfail = True
                if 'failure in xrdcp of Delphes' in line: copyfail = True
                if 'failure in xrdcp of ROOT' in line: transferfail = True
                if 'failure in DelphesCMSFWLite' in line: delphesfail = True
                if 'removing inputs' in line: finished += 1
            if copyfail:
                if verbose_level > 0:
                    print '\tXRDCP FAIL:',file,' and JobIndex:',index
                copy_fail+=1
                if resub_num == -1 or resub_num == 0: resub_index.append(index)
                continue
            if transferfail:
                if verbose_level > 0:
                    print '\tGFAL FAIL:',file,' and JobIndex:',index
                copy_fail+=1
                if resub_num == -1 or resub_num == 0: resub_index.append(index)
                continue
            if delphesfail:
                if verbose_level > 0:
                    print '\tDELPHES FAIL:',file,' and JobIndex:',index
                copy_fail+=1
                if resub_num == -1 or resub_num == 0: resub_index.append(index)
                continue
        except:
            pass

        try:
            current = open(dir + '/'+folder+'/'+file.replace('.jdl','.log'),'r')
            toolong = False
            memfail = False
            for line in current:
                if 'SYSTEM_PERIODIC_REMOVE due to job running for more than 2 days' in line:
                    toolong = True
                if 'SYSTEM_PERIODIC_REMOVE due to job exceeding requested memory' in line:
                    memfail = True
            if toolong:
                if verbose_level > 0:
                    print '\tWALLTIME FAIL:',file,' and JobIndex:',index
                time_fail+=1
                if resub_num == -1 or resub_num == 1: resub_index.append(index)
                continue
            if memfail:
                if verbose_level > 0:
                    print '\tMEMORY FAIL:',file,' and JobIndex:',index
                time_fail+=1
                if resub_num == -1 or resub_num == 1: resub_index.append(index)
                continue
        except:
            pass

        thisroot = ''
        for rootfile in rootfiles:
            if '_'+index+'.root' in rootfile: thisroot = rootfile

        if thisroot != '':
            continue
            # zerosize = EOSisZeroSizefile(rootdir+folder+'/'+thisroot,'Jun')
            # if zerosize:
            #     if verbose_level > 0:
            #         print '\tZERO SIZE:',file,' and JobIndex:',index
            #     size_fail+=1
            #     if resub_num == -1 or resub_num == 2: resub_index.append(index)
            #     continue
        else:
            if verbose_level > 0:
                print '\tNO ROOT:',file,' and JobIndex:',index
            no_roots+=1
            if resub_num == -1 or resub_num == 3: resub_index.append(index)
            continue

    print 'Percent done =',float(finished)/float(len(files))
    if resub_index != []: print 'RESUBS:', resub_index
    if resubmit != '1': continue

    savedir = os.getcwd()
    for index in resub_index:

        doSplitting = False ## assume for now that submission was already split up
        alreadySplit = True

        #if resub_num == 1: doSplitting = True

        if 'b' in index:
            doSplitting = False
            alreadySplit = True
        else:
            if os.path.exists(dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'.jdl') and os.path.exists(dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'b.jdl'):
                doSplitting = False
                alreadySplit = True

        if not doSplitting:
            print 'Not splitting '+folder.replace('_'+pileup,'')+ '_'+index+'.jdl'
            os.chdir(dir+'/'+folder)
            os.system('rm '+dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+ '_'+index+'.out')
            os.system('rm '+dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+ '_'+index+'.log')
            os.system('condor_submit '+dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'.jdl')
            os.chdir(savedir)

        else:
            if not alreadySplit:
                print 'Not split: Splitting '+index+'.jdl into '+index+'.jdl and '+index+'b.jdl'
                command = "grep 'Arguments' "+dir+"/"+folder+"/"+folder.replace("_"+pileup,"")+"_"+index+".jdl"
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
                (args, err) = proc.communicate()
                filename = (args.split(' ')[2])
                filename = filename[filename.find('/store'):]

                if len(args.split(' ')) > 6: args = args.replace(args.split(' ')[6]+' '+args.split(' ')[7],'')

                command = '/cvmfs/cms.cern.ch/common/dasgoclient --query="file='+filename+' | grep file.nevents" '
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
                (out, err) = proc.communicate()
                try: nevents = int(out.split('\n')[0])
                except:
                    try: nevents = int(out.split('\n')[1])
                    except: print 'ERROR: couldnt isolate the number of events'

                half1 = int(round(nevents/2))
                half2 = int(nevents-round(nevents/2))
                newargs1 = args.strip()+' 0 '+str(half1)
                newargs2 = args.strip()+' '+str(half1)+' '+str(half2)

                #print newargs1
                #print newargs2

                f = open(dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'.jdl','rU')
                jdllines = f.readlines()
                f.close()

                name = folder.replace('_'+pileup,'')+'_'+index
                newname = folder.replace('_'+pileup,'')+'_'+index+'b'

                with open(dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'.jdl','w') as fout:
                    for line in jdllines:
                        if 'Argument' in line: line = line.replace(args.strip(),newargs1)
                        fout.write(line)

                with open(dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'b.jdl','w') as fout:
                    for line in jdllines:
                        if 'Argument' in line: line = line.replace(args.strip(),newargs2)
                        if name in line: line = line.replace(name,newname)
                        fout.write(line)

                os.chdir(dir+'/'+folder)
                os.system('rm '+dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+ '_'+index+'.log')
                os.system('condor_submit '+dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'.jdl')
                os.system('condor_submit '+dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'b.jdl')
                os.chdir(savedir)

            else:
                print 'Is split: splitting '+index+'.jdl into '+index+'.jdl and '+index+'b.jdl'
                command = "grep 'Arguments' "+dir+"/"+folder+"/"+folder.replace("_"+pileup,"")+"_"+index+".jdl"
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
                (args, err) = proc.communicate()
                print args
                try:
                    origskip = int(args.split(' ')[6].strip())
                    origmax = int(args.split(' ')[7].strip())
                except:
                    print 'FIX ME'
                    continue

                newmax = origmax/2
                newskip = origskip+newmax

                #print args.replace(' '+str(origskip)+' '+str(origmax),' '+str(origskip)+' '+str(newmax))
                #print args.replace(' '+str(origskip)+' '+str(origmax),' '+str(newskip)+' '+str(newmax))

                f = open(dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'.jdl','rU')
                jdllines = f.readlines()
                f.close()

                name = folder.replace('_'+pileup,'')+'_'+index
                newname = folder.replace('_'+pileup,'')+'_'+index+'b'

                with open(dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'.jdl','w') as fout:
                    for line in jdllines:
                        if 'Argument' in line: line = line.replace(' '+str(origskip)+' '+str(origmax),' '+str(origskip)+' '+str(newmax))
                        fout.write(line)

                with open(dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'b.jdl','w') as fout:
                    for line in jdllines:
                        if 'Argument' in line: line = line.replace(' '+str(origskip)+' '+str(origmax),' '+str(newskip)+' '+str(newmax))
                        if name in line: line = line.replace(name,newname)
                        if '_2b00PU' in line: line = line.replace('_2b00PU','_200PU')
                        if '_20b0PU' in line: line = line.replace('_20b0PU','_200PU')
                        if '_200bPU' in line: line = line.replace('_200bPU','_200PU')
                        fout.write(line)

                os.chdir(dir+'/'+folder)
                os.system('rm '+dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+ '_'+index+'.log')
                os.system('condor_submit '+dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'.jdl')
                os.system('condor_submit '+dir+'/'+folder+'/'+folder.replace('_'+pileup,'')+'_'+index+'b.jdl')
                os.chdir(savedir)


print
print 'TOTAL JOBS: ', total_total
print 'ROOT files:', total_roots
print 'COPY FAIL:', copy_fail
print 'SYSTEM REMOVE:', time_fail
print 'ZERO SIZE:', size_fail
print 'NO ROOTS:', no_roots
print 'DONE:', total_total - copy_fail - time_fail - no_roots - size_fail
