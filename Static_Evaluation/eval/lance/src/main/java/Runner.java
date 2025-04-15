import com.github.gumtreediff.actions.EditScript;
import com.github.gumtreediff.actions.EditScriptGenerator;
import com.github.gumtreediff.actions.SimplifiedChawatheScriptGenerator;
import com.github.gumtreediff.gen.TreeGenerators;
import com.github.gumtreediff.matchers.MappingStore;
import com.github.gumtreediff.matchers.Matcher;
import com.github.gumtreediff.matchers.Matchers;
import com.github.gumtreediff.tree.Tree;
import com.github.gumtreediff.client.Run;
import com.opencsv.CSVWriter;


import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;


public class Runner {

    public static String getLogMessage(String logStmt){
        String items[] = logStmt.split(" ");

        int counter_start = 0 ;

        for(String token: items){
            if(!token.equals("(")){
                counter_start += 1;
            }
            else{
                break;
            }
        }

        int counter_end = items.length-1;
        for(int i=items.length-1;i>=0;i--){
            if(!items[i].equals(")")){
                counter_end -= 1;
            }
            else{
                break;
            }
        }

        String result = "";
        for(int i=counter_start;i<=counter_end;i++){
            result += items[i] + " ";
        }
        return result;
    }

    public static int getDifferenceLogLevel(String logStmtTarget, String logStmtPrediction){
        //Trace < Debug < Info < Warn < Error < Fatal.

        int cardinalTarget = 0;

        switch(logStmtTarget) {

            case "trace":
                // code block
                cardinalTarget = 1;
                break;

            case "debug":
                cardinalTarget = 2;
                break;

            case "info":
                cardinalTarget = 3;
                break;

            case "warn":
                cardinalTarget = 4;
                break;

            case "error":
                cardinalTarget = 5;
                break;

            case "fatal":
                cardinalTarget = 6;
                break;

            default:
                break;
        }

        int cardinalPrediction = 0;
        switch(logStmtPrediction) {

            case "trace":
                // code block
                cardinalPrediction = 1;
                break;

            case "debug":
                cardinalPrediction = 2;
                break;

            case "info":
                cardinalPrediction = 3;
                break;

            case "warn":
                cardinalPrediction = 4;
                break;

            case "error":
                cardinalPrediction = 5;
                break;

            case "fatal":
                cardinalPrediction = 6;
                break;

            default:
                break;
        }


        return Math.abs(cardinalTarget-cardinalPrediction);
    }


    /*
      log.trace("Trace Message!");
      log.debug("Debug Message!");
      log.info("Info Message!");
      log.warn("Warn Message!");
      log.error("Error Message!");
      log.fatal("Fatal Message!");
     */
    public static String getLevelLog(String logStmt){

        String extractedLevel = "";
        String [] tokensLogStmt = logStmt.split(" ");

        for(String token: tokensLogStmt){
            switch(token) {

                case "trace":
                    // code block
                    extractedLevel = "trace";
                    break;

                case "debug":
                    extractedLevel = "debug";
                    break;

                case "info":
                    extractedLevel = "info";
                    break;

                case "warn":
                    extractedLevel = "warn";
                    break;

                case "error":
                    extractedLevel = "error";
                    break;

                case "fatal":
                    extractedLevel = "fatal";
                    break;

//                case "log":
//                    extractedLevel = "log";
//                    break;
//
//                case "warning":
//                    extractedLevel = "warning";
//                    break;

                default:
                    break;
            }

        }



        return extractedLevel;
    }


    public static void main(String[] args) throws IOException {
        // Create a diff comparator with two inputs strings.

        Run.initGenerators(); // registers the available parsers

        List<String> input_list = Files.readAllLines(Paths.get("No-Pretraining/Analysis/wrong_input_test.txt"));
        List<String> target_list = Files.readAllLines(Paths.get("No-Pretraining/Analysis/wrong_target_test.txt"));
        List<String> prediction_list = Files.readAllLines(Paths.get("No-Pretraining/Analysis/wrong_prediction_test.txt"));
        List<String> log_stmt_list = Files.readAllLines(Paths.get("No-Pretraining/Analysis/wrong_log_stmt_test.txt"));


        int matchingLevel = 0;
        int matchingPosition = 0;
        int matchingMessage = 0;
        int unparsable_counter = 0;


        // Res files

        // create FileWriter object with file as parameter
        FileWriter predictedLog = new FileWriter("predictedLogsOnly.csv");
        FileWriter outputFileDistance = new FileWriter("logLevelDistance.csv");

        FileWriter correctLogLevelWriter = new FileWriter("correctLogLevel.csv");
        FileWriter correctLogPositionWriter = new FileWriter("correctLogPosition.csv");

        CSVWriter writerCorrectLevel = new CSVWriter(correctLogLevelWriter);
        String[] headerX = { "Instance Number", "Prediction", "Target"};
        writerCorrectLevel.writeNext(headerX);

        CSVWriter writerCorrectPosition = new CSVWriter(correctLogPositionWriter);
        String[] headerX1 = { "Instance Number", "Prediction", "Target" };
        writerCorrectPosition.writeNext(headerX1);

        FileWriter logLevelWriter = new FileWriter("logLevel.csv");
        FileWriter logPositionWriter = new FileWriter("logPosition.csv");

        FileWriter correctLogMessageWriter = new FileWriter("correctLogMessage.csv");


        // create CSVWriter object filewriter object as parameter

        CSVWriter writerLogPrediction = new CSVWriter(predictedLog);
        String[] header0 = { "Instance Number", "Prediction", "Target"};
        writerLogPrediction.writeNext(header0);

        CSVWriter writerLogLevel = new CSVWriter(logLevelWriter);
        String[] header1 = { "Instance Number", "Prediction", "Target" };
        writerLogLevel.writeNext(header1);

        CSVWriter writerLogPosition = new CSVWriter(logPositionWriter);
        String[] header2 = { "Instance Number", "Prediction", "Target" };
        writerLogPosition.writeNext(header2);


        CSVWriter writerLogMessage = new CSVWriter(correctLogMessageWriter);
        String[] header3 = { "Instance Number", "Prediction", "Target" };
        writerLogMessage.writeNext(header3);



        CSVWriter writerDistance = new CSVWriter(outputFileDistance);
        String[] header6 = { "Instance Number", "Prediction", "Target", "Distance" };
        writerDistance.writeNext(header6);



        ////////////////////


        List<String> logLevels = new ArrayList<>();
        logLevels.add("trace");
        logLevels.add("debug");
        logLevels.add("info");
        logLevels.add("warn");
        logLevels.add("error");
        logLevels.add("fatal");

        int itemsSize = prediction_list.size();


        for(int j = 0; j < itemsSize; j++) {

            String inputItem = input_list.get(j);
            String targetItem = target_list.get(j);
            String predItem = prediction_list.get(j);
            String logStmt = log_stmt_list.get(j);

            String flattenedLogStmt = String.join("",logStmt.split(" "));

            //Get logMessage for the target
            String targetLogMessage = String.join("",Runner.getLogMessage(logStmt).split(" "));

            //Get logLevel for the target
            String logLevelTarget = String.join("",Runner.getLevelLog(logStmt).split(" "));

            //Create folder for each input, target and prediction file
            String basePath = "Denoise-Files/Instance_"+j;

            File f1 = new File(basePath);
            boolean bool = f1.mkdir();

            //String basePath = "/Users/antonio/Desktop/NoPretraining-Files";

            String inputFile = basePath+"/input.java";
            String targetFile = basePath+"/target.java";
            String predFile = basePath+"/prediction.java";

            String classInputToWrite = "public class A { " +inputItem + " }";
            FileWriter myWriter = new FileWriter(inputFile,false);
            myWriter.write(classInputToWrite);
            myWriter.close();

            String classTargetToWrite="public class A { " +targetItem + " }";
            myWriter = new FileWriter(targetFile,false);
            myWriter.write(classTargetToWrite);
            myWriter.close();

            String classPredToWrite="public class A { " +predItem + " }";
            myWriter = new FileWriter(predFile,false);
            myWriter.write(classPredToWrite);
            myWriter.close();


            Tree input = TreeGenerators.getInstance().getTree(inputFile).getRoot();
            Tree target = TreeGenerators.getInstance().getTree(targetFile).getRoot();

            Tree prediciton;
            try {
                prediciton = TreeGenerators.getInstance().getTree(predFile).getRoot();
            }catch (Exception e){
                //Cannot construct the tree for the prediction, therefore we analyze this one with the CodeBleu
                unparsable_counter+=1;
                continue;

            }

            Matcher defaultMatcher = Matchers.getInstance().getMatcher(); // retrieves the default matcher

            MappingStore mappingsToTarget = defaultMatcher.match(input, target); // computes the mappings between the trees
            EditScriptGenerator editScriptGeneratorTarget = new SimplifiedChawatheScriptGenerator(); // instantiates the simplified Chawathe script generator
            EditScript actionsTarget = editScriptGeneratorTarget.computeActions(mappingsToTarget); // computes the edit script

            MappingStore mappingsToPrediction = defaultMatcher.match(input, prediciton); // computes the mappings between the trees
            EditScriptGenerator editScriptGeneratorPrediction = new SimplifiedChawatheScriptGenerator(); // instantiates the simplified Chawathe script generator
            EditScript actionsPrediction = editScriptGeneratorPrediction.computeActions(mappingsToPrediction); // computes the edit scrip

            if (actionsPrediction.size()==0){
                String[] data0 = {String.valueOf(j), "", logStmt};
                writerLogPrediction.writeNext(data0);
                continue;
            }

            int difference = Integer.MAX_VALUE;
            int targetEditAction = 0;

            int startPosTarget = -1;
            int endPosTarget = -1;


            for (int i = 0; i < actionsTarget.size(); i++) {

                int posStart1 = actionsTarget.get(i).getNode().getPos();
                int posEnd1 = actionsTarget.get(i).getNode().getEndPos();
                String sub = String.join("",classTargetToWrite.substring(posStart1,posEnd1).split(" "));
                if(sub.equals(flattenedLogStmt)){
                    startPosTarget = posStart1;
                    endPosTarget = posEnd1;
                    break;
                }

            }

            //picking the nearest edit action to the target one
            for (int i = 0; i < actionsPrediction.size(); i++) {

                int newRelativePosition = Math.abs(startPosTarget-actionsPrediction.get(i).getNode().getPos());
                if (newRelativePosition<difference);
                    difference = newRelativePosition;
                    targetEditAction = i;
            }

            int startPosPrediction = -1;
            int endPosPrediction = -1;

            startPosPrediction = actionsPrediction.get(targetEditAction).getNode().getPos();
            endPosPrediction = actionsPrediction.get(targetEditAction).getNode().getEndPos();

            String wrappedPred = "";
            String finalString = "";
            String[] itemsString = null;
            try {
                wrappedPred = "public class A { " + predItem + " }";
                finalString = wrappedPred.substring(startPosPrediction, endPosPrediction);
                itemsString = finalString.split(" ");
            }catch (Exception e){
                String[] data0 = {String.valueOf(j), finalString, logStmt};
                writerLogPrediction.writeNext(data0);
                continue;
            }

            String item0="";
            String item1="";
            String item2="";
            String itemLast="";

            try {
                item0 = itemsString[0].toLowerCase();
                item1 = itemsString[1].toLowerCase();
                item2 = itemsString[2].toLowerCase();
                itemLast = itemsString[itemsString.length - 1];
            }catch(Exception e){
                continue;
            }


            //writing The predicted log on txt File
            String[] data0 = {String.valueOf(j), finalString, logStmt};
            writerLogPrediction.writeNext(data0);


            if (((item2.contains("log") && item1.contains(".")) || (item0.contains("log") || item1.contains("log"))) && itemLast.contains(";")) {

                String logLevelPrediction = String.join("", Runner.getLevelLog(finalString).split(" "));
                String predLogMessage = String.join("", Runner.getLogMessage(finalString).split(" "));

                if(logLevelPrediction.equals("")) {

                    int startFrom = 0;
                    for (String token : finalString.split(" ")) {

                        if (token.equals("log") || token.equals("warning")) {
                            break;
                        }
                        startFrom += 1;
                    }
                    String [] subStr = finalString.substring(startFrom).split(" ");
                    String joinedString = "";

                    for(int k=startFrom+1; k<subStr.length-1; k++){
                        joinedString = joinedString + " " + subStr[k];
                    }

                    //Check here
                    int diff=-1;
                    String[] subArray = finalString.split(" ");
                    try {
                        for (String token : Arrays.copyOfRange(subArray, startFrom + 1, subArray.length - 1)) {
                            if (logLevels.contains(token)) {
                                diff = getDifferenceLogLevel(logLevelTarget, token);
                                logLevelPrediction = token;
                            }
                        }
                    }catch(Exception e){
                        logLevelPrediction="";
                        System.out.println(j);
                    }

                }

                //Retrieve correct cardinal difference only for those log for which there is a Log4J mapping
                if(!logLevelTarget.equals("log") && !logLevelTarget.equals("warning") && !logLevelPrediction.equals("")) {

                    int distance = getDifferenceLogLevel(logLevelTarget, logLevelPrediction);
                    String[] data1 = {String.valueOf(j), logLevelPrediction, logLevelTarget, String.valueOf(distance)};
                    writerDistance.writeNext(data1);

                    if (startPosPrediction == startPosTarget) {
                        String [] data2 = {String.valueOf(j), predItem, targetItem};
                        writerLogPosition.writeNext(data2);
                        writerCorrectPosition.writeNext(data2);
                        matchingPosition += 1;
                    }else{
                        String offsetTarget = classTargetToWrite.substring(17,startPosTarget);
                        String offsetPrediction = "";
                        if (startPosPrediction==0){
                            offsetPrediction = wrappedPred.substring(17);
                            System.out.println(j);
                        }
                        else{
                            offsetPrediction = wrappedPred.substring(17,startPosPrediction);
                        }

                        String[] data3 = {String.valueOf(j), predItem, targetItem, offsetPrediction, offsetTarget};
                        writerLogPosition.writeNext(data3);
                    }

                    // We have a matching level. Keep track of those one
                    if (logLevelPrediction.equals(logLevelTarget)) {
                        matchingLevel += 1;
                        String[] data = {String.valueOf(j), finalString, logLevelTarget};
                        writerLogLevel.writeNext(data);
                        writerCorrectLevel.writeNext(data);
                    }

                    if (predLogMessage.equals(targetLogMessage)) {
                        matchingMessage += 1;
                        String[] data = {String.valueOf(j), finalString, targetLogMessage};
                        writerLogMessage.writeNext(data);
                    }
                }

//                // We have a matching level. Keep track of those one
//                if (logLevelPrediction.equals(logLevelTarget)) {
//                    matchingLevel += 1;
//                    String[] data1 = {String.valueOf(j), finalString, logLevelTarget};
//                    writerLogLevel.writeNext(data1);
//                }
//
//                if (predLogMessage.equals(targetLogMessage)) {
//                    matchingMessage += 1;
//                    String[] data1 = {String.valueOf(j), finalString, targetLogMessage};
//                    writerLogMessage.writeNext(data1);
//                }
            }
        }

        logLevelWriter.close();
        logPositionWriter.close();
        writerDistance.close();
        writerLogPrediction.close();
        writerCorrectLevel.close();
        writerCorrectPosition.close();
        correctLogMessageWriter.close();

        //Perfect predictions denoise-task
        //int perfectPredictionNums = 1828;

        //Perfect predictions logstmt-task
        //int perfectPredictionNums = 1483;

        //Perfect predictions multi-task
        //int perfectPredictionNums = 1481;

        //Perfect predictions no-pretraining
        int perfectPredictionNums = 1526;

        double percentagePositionCorrect = ( (perfectPredictionNums + (double) matchingPosition) / 12020) * 100;
        double percentageLevelCorrect = ( (perfectPredictionNums + (double )matchingLevel) / 12020) * 100;
        double percentageMessageCorrect = ( (perfectPredictionNums + (double )matchingMessage) / 12020) * 100;
        double percentageUnparsable =  ( ( (double) unparsable_counter) /12020) * 100;

        System.out.println("Not Parsable: " + unparsable_counter + "/" + 12020 + " :" + percentageUnparsable);
        System.out.println("Perfect prediction LEVEL: "+ (perfectPredictionNums+matchingLevel) + "/" + 12020 + " :" + percentageLevelCorrect);
        System.out.println("Perfect prediction POS: "+(perfectPredictionNums+matchingPosition) + "/" + 12020 + " :" + percentagePositionCorrect);
        System.out.println("Perfect prediction MESSAGE: "+(perfectPredictionNums + matchingMessage) + "/" + 12020 + " :" + percentageMessageCorrect);

    }
}
